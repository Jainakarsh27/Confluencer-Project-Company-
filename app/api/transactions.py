from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionHistoryResponse,
)
from app.schemas.common import ErrorResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/accounts", tags=["Transactions"])


@router.post(
    "/{account_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a transaction (Credit or Debit)",
    description=(
        "Executes an atomic transaction for the specified account. "
        "Credits increase the balance; Debits decrease the balance if sufficient funds exist. "
        "Rejects duplicate reference_id within the same account with 409 Conflict. "
        "Rejects overdraft debits with 422 Unprocessable Entity."
    ),
    responses={
        201: {"description": "Transaction successfully posted"},
        404: {"model": ErrorResponse, "description": "Account not found"},
        409: {"model": ErrorResponse, "description": "Duplicate reference ID within this account"},
        422: {"model": ErrorResponse, "description": "Insufficient funds or invalid transaction parameters"},
    },
)
def add_transaction(
    account_id: str,
    tx_in: TransactionCreate,
    db: Session = Depends(get_db)
) -> TransactionResponse:
    tx, new_balance = TransactionService.add_transaction(db, account_id, tx_in)
    resp = TransactionResponse.model_validate(tx)
    resp.resulting_balance = str(new_balance)
    return resp


@router.get(
    "/{account_id}/transactions",
    response_model=TransactionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get transaction history",
    description=(
        "Fetches paginated transaction history for an account, sorted latest-first. "
        "Supports optional filtering by transaction type (credit/debit)."
    ),
    responses={
        200: {"description": "Transaction history retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Account not found"},
        422: {"model": ErrorResponse, "description": "Invalid query parameters"},
    },
)
def get_transaction_history(
    account_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    type: Optional[str] = Query(None, description="Optional filter by type: credit or debit"),
    db: Session = Depends(get_db)
) -> TransactionHistoryResponse:
    result = TransactionService.get_transaction_history(
        db,
        account_id=account_id,
        page=page,
        limit=limit,
        tx_type=type
    )
    return TransactionHistoryResponse(
        items=[TransactionResponse.model_validate(t) for t in result["items"]],
        pagination=result["pagination"]
    )
