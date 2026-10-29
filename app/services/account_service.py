from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.account import Account
from app.schemas.account import AccountCreate
from app.exceptions import AccountNotFoundException
from app.core.logging import logger


class AccountService:
    @staticmethod
    def create_account(db: Session, account_in: AccountCreate) -> Account:
        """Create a new account with guaranteed zero initial balance."""
        account = Account(
            name=account_in.name,
            balance=Decimal("0.00")
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        logger.info("Created account id=%s name='%s' with balance=0.00", account.id, account.name)
        return account

    @staticmethod
    def get_account(db: Session, account_id: str) -> Account:
        """Fetch an account by ID, raising AccountNotFoundException if not found."""
        stmt = select(Account).where(Account.id == account_id)
        account = db.execute(stmt).scalar_one_or_none()
        if not account:
            raise AccountNotFoundException(account_id=account_id)
        return account

    @staticmethod
    def get_balance(db: Session, account_id: str) -> Decimal:
        """Fetch the current balance of an account."""
        account = AccountService.get_account(db, account_id)
        return account.balance

    @staticmethod
    def list_all_accounts(db: Session, limit: int = 50) -> List[Account]:
        """List all accounts for dashboard switching and administrative views."""
        stmt = select(Account).order_by(Account.created_at.desc()).limit(limit)
        return list(db.execute(stmt).scalars().all())
