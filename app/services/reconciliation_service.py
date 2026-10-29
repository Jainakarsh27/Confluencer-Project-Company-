from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.common import ReconciliationResponse
from app.exceptions import AccountNotFoundException
from app.schemas.account import format_decimal


class ReconciliationService:
    @staticmethod
    def reconcile_account(db: Session, account_id: str) -> ReconciliationResponse:
        """
        Audits an account's persisted balance against the full ledger of posted transactions.
        Ensures balance == Sum(Credits) - Sum(Debits).
        Does NOT alter account balance. Read-only diagnostic verification.
        """
        stmt_account = select(Account).where(Account.id == account_id)
        account = db.execute(stmt_account).scalar_one_or_none()
        if not account:
            raise AccountNotFoundException(account_id=account_id)

        # Sum credits
        credit_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.account_id == account_id,
                Transaction.type == "credit"
            )
        )
        total_credits = Decimal(str(db.execute(credit_stmt).scalar() or 0))

        # Sum debits
        debit_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.account_id == account_id,
                Transaction.type == "debit"
            )
        )
        total_debits = Decimal(str(db.execute(debit_stmt).scalar() or 0))

        # Transaction count
        count_stmt = select(func.count(Transaction.id)).where(Transaction.account_id == account_id)
        tx_count = db.execute(count_stmt).scalar() or 0

        calculated_balance = total_credits - total_debits
        is_consistent = (calculated_balance == account.balance)

        return ReconciliationResponse(
            account_id=account.id,
            stored_balance=format_decimal(account.balance),
            calculated_balance=format_decimal(calculated_balance),
            is_consistent=is_consistent,
            total_credits=format_decimal(total_credits),
            total_debits=format_decimal(total_debits),
            transaction_count=tx_count,
            checked_at=datetime.now(timezone.utc)
        )
