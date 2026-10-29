from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.logging import logger


class LedgerException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AccountNotFoundException(LedgerException):
    def __init__(self, account_id: str):
        super().__init__(
            code="ACCOUNT_NOT_FOUND",
            message=f"Account '{account_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class DuplicateTransactionException(LedgerException):
    def __init__(self, reference_id: str, existing_transaction_id: Optional[str] = None):
        super().__init__(
            code="DUPLICATE_TRANSACTION",
            message=f"A transaction with reference_id '{reference_id}' already exists for this account.",
            status_code=status.HTTP_409_CONFLICT,
            details={"existing_transaction_id": existing_transaction_id} if existing_transaction_id else None,
        )


class InsufficientFundsException(LedgerException):
    def __init__(self, balance: Any, amount: Any):
        super().__init__(
            code="INSUFFICIENT_FUNDS",
            message=f"The account does not have sufficient balance. Current balance: {balance}, requested debit: {amount}.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"current_balance": str(balance), "requested_amount": str(amount)},
        )


class InvalidTransactionException(LedgerException):
    def __init__(self, message: str):
        super().__init__(
            code="INVALID_TRANSACTION",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LedgerException)
    async def ledger_exception_handler(request: Request, exc: LedgerException) -> JSONResponse:
        content = {
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
        if exc.details:
            content["error"]["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            errors.append({"field": loc, "message": err.get("msg", "Invalid value")})
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request body or parameters failed validation.",
                    "details": errors,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact system support.",
                }
            },
        )
