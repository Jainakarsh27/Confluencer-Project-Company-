import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.account import Account


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True
    )

    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="transactions"
    )

    __table_args__ = (
        UniqueConstraint("account_id", "reference_id", name="uq_account_reference_id"),
        CheckConstraint("amount > 0", name="chk_transaction_amount_positive"),
        CheckConstraint("type IN ('credit', 'debit')", name="chk_transaction_type_valid"),
        Index("ix_transactions_account_created", "account_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, account_id={self.account_id}, type={self.type}, amount={self.amount}, ref={self.reference_id})>"
