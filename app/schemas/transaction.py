from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.common import PaginationMetadata


def format_decimal(value: Any) -> str:
    if value is None:
        return "0.00"
    return f"{Decimal(value):.2f}"


class TransactionCreate(BaseModel):
    type: Literal["credit", "debit"] = Field(
        ...,
        description="Transaction type, must be 'credit' or 'debit'"
    )
    amount: Decimal = Field(
        ...,
        description="Positive transaction amount with at most two decimal places"
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Description of the transaction"
    )
    reference_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique transaction reference for this account"
    )

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount_input(cls, v: Any) -> Decimal:
        if v is None:
            raise ValueError("Amount is required.")
        try:
            val = Decimal(str(v).strip())
        except (InvalidOperation, TypeError):
            raise ValueError("Amount must be a valid numeric decimal value.")

        if val.is_nan() or val.is_infinite():
            raise ValueError("Amount must be a finite number.")

        if val <= Decimal("0.00"):
            raise ValueError("Transaction amount must be strictly greater than zero.")

        # Check precision: at most 2 decimal places
        # Decimal.as_tuple().exponent gives negative count of decimal digits
        exponent = val.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            raise ValueError("Amount cannot have more than two decimal places.")

        return val

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Description cannot be empty or contain only whitespace.")
        return stripped

    @field_validator("reference_id")
    @classmethod
    def validate_reference_id(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Reference ID cannot be empty or contain only whitespace.")
        return stripped

    model_config = ConfigDict(extra="forbid")


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    type: str
    amount: str
    description: str
    reference_id: str
    created_at: datetime
    resulting_balance: Optional[str] = None

    @field_validator("amount", mode="before")
    @classmethod
    def serialize_amount(cls, v: Any) -> str:
        return format_decimal(v)

    @field_validator("resulting_balance", mode="before")
    @classmethod
    def serialize_resulting_balance(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return format_decimal(v)

    model_config = ConfigDict(from_attributes=True)


class TransactionHistoryResponse(BaseModel):
    items: List[TransactionResponse]
    pagination: PaginationMetadata
