from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


def format_decimal(value: Optional[Decimal]) -> str:
    if value is None:
        return "0.00"
    return f"{Decimal(value):.2f}"


class AccountCreate(BaseModel):
    name: str = Field(..., description="Account holder name", min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Account name cannot be empty or contain only whitespace.")
        return stripped

    model_config = ConfigDict(extra="forbid")


class AccountResponse(BaseModel):
    id: str
    name: str
    balance: str
    created_at: datetime

    @field_validator("balance", mode="before")
    @classmethod
    def serialize_balance(cls, v: Any) -> str:
        return format_decimal(v)

    model_config = ConfigDict(from_attributes=True)


class AccountBalanceResponse(BaseModel):
    account_id: str
    balance: str

    @field_validator("balance", mode="before")
    @classmethod
    def serialize_balance(cls, v: Any) -> str:
        return format_decimal(v)

    model_config = ConfigDict(from_attributes=True)
