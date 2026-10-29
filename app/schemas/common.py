from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorPayload


class PaginationMetadata(BaseModel):
    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Page size / maximum items per page")
    total_records: int = Field(..., description="Total matching records count")
    total_pages: int = Field(..., description="Total number of pages available")


class ReconciliationResponse(BaseModel):
    account_id: str
    stored_balance: str
    calculated_balance: str
    is_consistent: bool
    total_credits: str
    total_debits: str
    transaction_count: int
    checked_at: datetime
