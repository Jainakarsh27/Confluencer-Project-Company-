import math
import threading
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.schemas.common import PaginationMetadata
from app.exceptions import (
    AccountNotFoundException,
    DuplicateTransactionException,
    InsufficientFundsException,
    InvalidTransactionException,
)
from app.core.logging import logger

# Thread synchronization locks per account for in-process & SQLite concurrency safety
_account_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
_global_lock = threading.Lock()


def get_account_lock(account_id: str) -> threading.Lock:
    with _global_lock:
        return _account_locks[account_id]


class TransactionService:
    @staticmethod
    def add_transaction(
        db: Session,
        account_id: str,
        tx_in: TransactionCreate
    ) -> Tuple[Transaction, Decimal]:
        """
        Executes an atomic credit or debit transaction on an account with dual-layer concurrency protection:
        1. Thread synchronization mutex (protects SQLite in-memory and multi-threaded execution).
        2. Database row-level lock (SELECT ... FOR UPDATE) for multi-process PostgreSQL.
        3. Database-level composite unique constraint (uq_account_reference_id) as the final defense.
        """
        account_lock = get_account_lock(account_id)
        with account_lock:
            try:
                # 1. Fetch account with row-level lock if supported by the database dialect
                stmt = select(Account).where(Account.id == account_id)
                if db.bind and db.bind.dialect.name == "postgresql":
                    stmt = stmt.with_for_update()

                account = db.execute(stmt).scalar_one_or_none()
                if not account:
                    raise AccountNotFoundException(account_id=account_id)

                # 2. Check for duplicate reference_id within this account
                dup_stmt = select(Transaction).where(
                    and_(
                        Transaction.account_id == account_id,
                        Transaction.reference_id == tx_in.reference_id
                    )
                )
                existing_tx = db.execute(dup_stmt).scalar_one_or_none()
                if existing_tx:
                    logger.warning(
                        "Duplicate transaction detected: account_id=%s, reference_id=%s",
                        account_id,
                        tx_in.reference_id
                    )
                    raise DuplicateTransactionException(
                        reference_id=tx_in.reference_id,
                        existing_transaction_id=existing_tx.id
                    )

                # 3. Validate business rules for credit vs debit
                if tx_in.type == "debit":
                    if account.balance < tx_in.amount:
                        logger.warning(
                            "Insufficient funds: account_id=%s balance=%s requested=%s",
                            account_id,
                            account.balance,
                            tx_in.amount
                        )
                        raise InsufficientFundsException(
                            balance=account.balance,
                            amount=tx_in.amount
                        )
                    new_balance = account.balance - tx_in.amount
                elif tx_in.type == "credit":
                    new_balance = account.balance + tx_in.amount
                else:
                    raise InvalidTransactionException(f"Invalid transaction type: {tx_in.type}")

                # 4. Create the immutable transaction record
                tx = Transaction(
                    account_id=account.id,
                    type=tx_in.type,
                    amount=tx_in.amount,
                    description=tx_in.description,
                    reference_id=tx_in.reference_id,
                )
                db.add(tx)

                # 5. Atomically update the account balance
                account.balance = new_balance

                # 6. Commit unit of work
                db.commit()
                db.refresh(tx)
                db.refresh(account)

                logger.info(
                    "Transaction posted: tx_id=%s account_id=%s type=%s amount=%s new_balance=%s ref=%s",
                    tx.id,
                    account.id,
                    tx.type,
                    tx.amount,
                    account.balance,
                    tx.reference_id
                )
                return tx, account.balance

            except IntegrityError as exc:
                db.rollback()
                logger.warning(
                    "IntegrityError on transaction insert (concurrency conflict): %s",
                    exc
                )
                raise DuplicateTransactionException(reference_id=tx_in.reference_id)
            except Exception:
                db.rollback()
                raise

    @staticmethod
    def get_transaction_history(
        db: Session,
        account_id: str,
        page: int = 1,
        limit: int = 10,
        tx_type: Optional[str] = None
    ) -> Dict:
        """
        Retrieves paginated, filtered transaction history sorted newest first.
        """
        # Ensure account exists first
        stmt_account = select(Account.id).where(Account.id == account_id)
        if not db.execute(stmt_account).scalar_one_or_none():
            raise AccountNotFoundException(account_id=account_id)

        # Base filter condition
        filters = [Transaction.account_id == account_id]
        if tx_type:
            cleaned_type = tx_type.strip().lower()
            if cleaned_type not in ("credit", "debit"):
                raise InvalidTransactionException("Transaction type filter must be 'credit' or 'debit'.")
            filters.append(Transaction.type == cleaned_type)

        # 1. Total matching count
        count_stmt = select(func.count(Transaction.id)).where(and_(*filters))
        total_records = db.execute(count_stmt).scalar() or 0

        # 2. Total pages calculation
        total_pages = math.ceil(total_records / limit) if total_records > 0 else 0

        # 3. Paginated query with deterministic sorting (created_at DESC, id DESC)
        offset = (page - 1) * limit
        query = (
            select(Transaction)
            .where(and_(*filters))
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(db.execute(query).scalars().all())

        return {
            "items": items,
            "pagination": PaginationMetadata(
                page=page,
                limit=limit,
                total_records=total_records,
                total_pages=total_pages
            )
        }
