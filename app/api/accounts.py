from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.account import (
    AccountCreate,
    AccountResponse,
    AccountBalanceResponse,
)
from app.schemas.common import ErrorResponse, ReconciliationResponse
from app.services.account_service import AccountService
from app.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
    description="Creates a new account with a strictly zero initial balance. Client cannot set the starting balance.",
    responses={
        201: {"description": "Account successfully created"},
        422: {"model": ErrorResponse, "description": "Validation error (e.g. blank name)"},
    },
)
def create_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db)
) -> AccountResponse:
    account = AccountService.create_account(db, account_in)
    return AccountResponse.model_validate(account)


@router.get(
    "",
    response_model=List[AccountResponse],
    status_code=status.HTTP_200_OK,
    summary="List accounts",
    description="Returns recent accounts for dashboard view and testing.",
)
def list_accounts(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[AccountResponse]:
    accounts = AccountService.list_all_accounts(db, limit=limit)
    return [AccountResponse.model_validate(a) for a in accounts]


@router.get(
    "/{account_id}/balance",
    response_model=AccountBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current account balance",
    description="Fetches the current real-time balance of an account.",
    responses={
        200: {"description": "Current account balance retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Account not found"},
    },
)
def get_balance(
    account_id: str,
    db: Session = Depends(get_db)
) -> AccountBalanceResponse:
    balance = AccountService.get_balance(db, account_id)
    return AccountBalanceResponse(account_id=account_id, balance=balance)


@router.get(
    "/{account_id}/reconciliation",
    response_model=ReconciliationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reconcile account balance against ledger",
    description="Audits the stored account balance against the arithmetic sum of all posted transactions (Credits - Debits).",
    responses={
        200: {"description": "Reconciliation check completed successfully"},
        404: {"model": ErrorResponse, "description": "Account not found"},
    },
)
def reconcile_account(
    account_id: str,
    db: Session = Depends(get_db)
) -> ReconciliationResponse:
    return ReconciliationService.reconcile_account(db, account_id)


@router.post(
    "/system/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset database to clean slate",
    description="Wipes all test accounts and transactions so a recruiter or evaluator can start with fresh data.",
)
def reset_database(db: Session = Depends(get_db)):
    from sqlalchemy import delete
    from app.models.transaction import Transaction
    from app.models.account import Account
    
    db.execute(delete(Transaction))
    db.execute(delete(Account))
    db.commit()
    return {"message": "Database reset successfully. Fresh slate ready for recruiter demo."}
