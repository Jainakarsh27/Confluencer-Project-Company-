import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List
from sqlalchemy import String, Numeric, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="desc(Transaction.created_at)"
    )

    __table_args__ = (
        CheckConstraint("balance >= 0", name="chk_account_balance_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name='{self.name}', balance={self.balance})>"
