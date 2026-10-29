# LedgerFlow — Production Transaction Ledger API & Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-22%20Passed-brightgreen.svg)]()

LedgerFlow is an enterprise-grade Transaction Ledger System designed with double-entry precision, atomic concurrency protection, idempotency enforcement, and financial auditability.

---

## 🌟 Key Features

- **Strict Zero Initial Balance**: Accounts are created with an immutable starting balance of `0.00`. Client attempts to specify an initial balance are rejected.
- **Double-Entry Style Atomic Units of Work**: Balance updates and immutable transaction logs commit or rollback together in a single database transaction.
- **Pessimistic Concurrency Protection**: Multi-threaded and multi-process row locking (`SELECT ... FOR UPDATE`) guarantees balances never drop below zero, even during simultaneous overdraft debits.
- **Database-Enforced Idempotency**: Composite unique constraint `(account_id, reference_id)` prevents double-charging and duplicate transactions with HTTP 409 Conflict.
- **Zero Floating-Point Financial Precision**: Strict use of Python `Decimal` and PostgreSQL `NUMERIC(18,2)` eliminates binary rounding drift.
- **Deterministic Pagination & Filtering**: Database-level filtering and pagination (`LIMIT`/`OFFSET`) ordered deterministically by `created_at DESC, id DESC`.
- **Read-Only Ledger Reconciliation Service**: Diagnostic endpoint audits stored account balance against arithmetic sum of all posted transactions ($\sum \text{Credits} - \sum \text{Debits}$).
- **Interactive Full-Stack Web Dashboard**: Built-in fintech dark-mode UI with live balance sync, account switcher, transaction modals, and real-time chaos testing simulators (overdraft, duplicates, 5x concurrency races).

---

## 🛠️ Technology Stack

| Layer | Component | Description |
|---|---|---|
| **API Framework** | FastAPI (Python 3.12+) | Async REST endpoints, automatic OpenAPI/Swagger docs, Pydantic validation |
| **ORM & DB Engine** | SQLAlchemy 2.0 | Explicit transaction boundaries, pessimistic locking, connection pooling |
| **Database** | PostgreSQL 16 (or SQLite) | Relational persistence, foreign key cascades, check constraints, composite uniqueness |
| **Migrations** | Alembic | Version-controlled database schema migrations |
| **Testing** | Pytest + Starlette TestClient | 22 comprehensive unit, integration, integrity, and multi-threaded concurrency tests |
| **Frontend** | Vanilla SPA (ES6 + CSS3) | High-performance, zero-dependency modern dashboard mounted directly by FastAPI |
| **Containerization**| Docker & Docker Compose | Multi-stage Dockerfile and orchestrated Compose environment with health checks |

---

## 📁 Repository Structure

```
ledgerflow/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, CORS, and static mount
│   ├── core/
│   │   ├── config.py            # Environment settings (pydantic-settings)
│   │   └── logging.py           # Structured logging configuration
│   ├── db/
│   │   ├── base.py              # DeclarativeBase
│   │   └── session.py           # SQLAlchemy 2.0 engine & session dependency
│   ├── models/
│   │   ├── account.py           # Account ORM model (UUID, check balance >= 0)
│   │   └── transaction.py       # Transaction ORM model (UUID, composite unique ref)
│   ├── schemas/
│   │   ├── account.py           # Account input/output Pydantic schemas
│   │   ├── transaction.py       # Transaction input/output schemas with Decimal validation
│   │   └── common.py            # Error format, Pagination, Reconciliation schemas
│   ├── api/
│   │   ├── accounts.py          # Account endpoints (Create, Balance, Reconciliation)
│   │   └── transactions.py      # Transaction endpoints (Credit/Debit, History)
│   ├── services/
│   │   ├── account_service.py   # Account creation and balance logic
│   │   ├── transaction_service.py # Atomic unit of work, row locking, duplicate checks
│   │   └── reconciliation_service.py # Sum(credits) - Sum(debits) audit check
│   ├── exceptions.py            # Custom exceptions and centralized HTTP exception handlers
│   └── static/                  # Built-in full-featured web dashboard
│       ├── index.html
│       ├── style.css
│       └── app.js
├── alembic/                     # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── tests/                       # Automated test suite
│   ├── conftest.py              # Isolated DB fixtures and test client
│   ├── test_accounts.py         # Account creation, validation, balance tests
│   ├── test_transactions.py     # Credit, debit, overdraft rejection, duplicate tests
│   ├── test_history.py          # Filtering, pagination, sorting tests
│   ├── test_integrity.py        # Immutability, rollback consistency, reconciliation
│   └── test_concurrency.py      # Multi-threaded concurrent debits & duplicate races
├── docs/
│   └── design-decisions.md      # Deep-dive into technical trade-offs and rationale
├── Dockerfile                   # Multi-stage production container
├── compose.yaml                 # PostgreSQL 16 + FastAPI service
├── postman_collection.json      # Postman test collection with scripts
├── alembic.ini                  # Alembic configuration
├── requirements.txt             # Project dependencies
├── .env.example                 # Environment configuration template
└── README.md
```

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.12 or newer
- Git

### 2. Clone and Setup Environment
```bash
# Clone the repository
git clone <repo-url>
cd ledgerflow

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```
*By default, `.env` is configured to use `sqlite:///./ledgerflow.db` for zero-configuration instant local development.*

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Start the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Docker Compose Setup (PostgreSQL 16)

To run the complete stack backed by a PostgreSQL 16 container:

```bash
docker compose up --build
```
This automatically boots:
1. PostgreSQL 16 on port `5432` with a persistent volume.
2. LedgerFlow API on port `8000`, running migrations before starting uvicorn.

---

## 🧪 Running Automated Tests

Run the full test suite with verbose reporting:

```bash
pytest -v
```

All 22 tests run in isolated in-memory test databases:
```
tests/test_accounts.py ......                                            [ 27%]
tests/test_concurrency.py ..                                             [ 36%]
tests/test_history.py ......                                             [ 63%]
tests/test_integrity.py ..                                               [ 72%]
tests/test_transactions.py ......                                        [100%]

======================= 22 passed, 7 warnings in 2.29s ========================
```

---

## 📖 API Reference & Examples

### 1. Create Account
**Endpoint**: `POST /api/v1/accounts`

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Akarsh Jain"}'
```

**Response (201 Created)**:
```json
{
  "id": "e936cf0d-27ad-4560-b6bc-fbb4d445c086",
  "name": "Akarsh Jain",
  "balance": "0.00",
  "created_at": "2026-10-27T18:30:00Z"
}
```

---

### 2. Post Credit Transaction
**Endpoint**: `POST /api/v1/accounts/{account_id}/transactions`

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/accounts/e936cf0d-27ad-4560-b6bc-fbb4d445c086/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": "100.00",
    "description": "Initial deposit",
    "reference_id": "DEP-001"
  }'
```

**Response (201 Created)**:
```json
{
  "id": "c1f7a188-75b5-4b05-9fa8-18e596bb3101",
  "account_id": "e936cf0d-27ad-4560-b6bc-fbb4d445c086",
  "type": "credit",
  "amount": "100.00",
  "description": "Initial deposit",
  "reference_id": "DEP-001",
  "created_at": "2026-10-27T18:31:00Z",
  "resulting_balance": "100.00"
}
```

---

### 3. Post Debit Transaction
**Endpoint**: `POST /api/v1/accounts/{account_id}/transactions`

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/accounts/e936cf0d-27ad-4560-b6bc-fbb4d445c086/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "debit",
    "amount": "30.00",
    "description": "Coffee & Book purchase",
    "reference_id": "PUR-001"
  }'
```

**Response (201 Created)**:
```json
{
  "id": "d2e8b299-86c6-4c16-0fb9-29f607cc4212",
  "account_id": "e936cf0d-27ad-4560-b6bc-fbb4d445c086",
  "type": "debit",
  "amount": "30.00",
  "description": "Coffee & Book purchase",
  "reference_id": "PUR-001",
  "created_at": "2026-10-27T18:32:00Z",
  "resulting_balance": "70.00"
}
```

---

### 4. Overdraft Debit Rejection (Insufficient Funds)
Attempting to debit ₹150.00 when the available balance is only ₹70.00:

**Response (422 Unprocessable Content)**:
```json
{
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "The account does not have sufficient balance. Current balance: 70.00, requested debit: 150.00.",
    "details": {
      "current_balance": "70.00",
      "requested_amount": "150.00"
    }
  }
}
```
*The account balance remains unchanged at 70.00, and no transaction record is created.*

---

### 5. Duplicate Transaction Rejection
Submitting reference `DEP-001` again for the same account:

**Response (409 Conflict)**:
```json
{
  "error": {
    "code": "DUPLICATE_TRANSACTION",
    "message": "A transaction with reference_id 'DEP-001' already exists for this account.",
    "details": {
      "existing_transaction_id": "c1f7a188-75b5-4b05-9fa8-18e596bb3101"
    }
  }
}
```

---

### 6. Get Account Balance
**Endpoint**: `GET /api/v1/accounts/{account_id}/balance`

**Response (200 OK)**:
```json
{
  "account_id": "e936cf0d-27ad-4560-b6bc-fbb4d445c086",
  "balance": "70.00"
}
```

---

### 7. Get Transaction History
**Endpoint**: `GET /api/v1/accounts/{account_id}/transactions?page=1&limit=10&type=credit`

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "c1f7a188-75b5-4b05-9fa8-18e596bb3101",
      "account_id": "e936cf0d-27ad-4560-b6bc-fbb4d445c086",
      "type": "credit",
      "amount": "100.00",
      "description": "Initial deposit",
      "reference_id": "DEP-001",
      "created_at": "2026-10-27T18:31:00Z",
      "resulting_balance": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total_records": 1,
    "total_pages": 1
  }
}
```

---

### 8. Run Ledger Balance Reconciliation Audit
**Endpoint**: `GET /api/v1/accounts/{account_id}/reconciliation`

**Response (200 OK)**:
```json
{
  "account_id": "e936cf0d-27ad-4560-b6bc-fbb4d445c086",
  "stored_balance": "70.00",
  "calculated_balance": "70.00",
  "is_consistent": true,
  "total_credits": "100.00",
  "total_debits": "30.00",
  "transaction_count": 2,
  "checked_at": "2026-10-27T18:35:00Z"
}
```

---

## 🎯 Assessment Requirements Checklist

| Requirement | Implementation | Automated Test |
|---|---|---|
| **Account Creation** | Server UUID, UTC timestamp, strictly 0.00 balance | `tests/test_accounts.py::test_create_account_success` |
| **No Client Initial Balance** | Request schema forbids client-supplied balance | `tests/test_accounts.py::test_create_account_initial_balance_cannot_be_set_by_client` |
| **Required & Validated Name** | Rejects missing/blank/whitespace names with 422 | `tests/test_accounts.py::test_create_account_rejects_whitespace_name` |
| **Atomic Credit** | Atomically increases balance and logs transaction | `tests/test_transactions.py::test_credit_transaction_updates_balance` |
| **Atomic Debit** | Atomically decreases balance if funds sufficient | `tests/test_transactions.py::test_debit_transaction_updates_balance` |
| **Insufficient Funds** | Rejects debit > balance with 422 `INSUFFICIENT_FUNDS`, 0 balance mutation | `tests/test_transactions.py::test_debit_insufficient_funds_rejected` |
| **Duplicate Prevention** | Unique `(account_id, reference_id)` constraint; 409 conflict | `tests/test_transactions.py::test_duplicate_reference_id_rejected` |
| **Multi-Tenant References**| Same reference allowed on different accounts | `tests/test_transactions.py::test_same_reference_id_allowed_on_different_accounts` |
| **Balance Endpoint** | Fast real-time balance retrieval with 404 handling | `tests/test_accounts.py::test_get_balance_success` |
| **History Filtering** | Filters by `credit` or `debit` or returns both | `tests/test_history.py::test_filter_by_type_credit` |
| **Database Pagination** | `page`, `limit`, `total_records`, `total_pages` metadata | `tests/test_history.py::test_pagination_pages_and_limits` |
| **Deterministic Sorting** | Sorted newest first (`created_at DESC, id DESC`) | `tests/test_history.py::test_get_history_all_sorted_newest_first` |
| **Transaction Immutability**| No PUT/PATCH/DELETE endpoints exposed | `tests/test_integrity.py::test_transaction_immutability_no_update_or_delete_routes` |
| **Ledger Consistency** | Arithmetic sum of journal equals stored balance | `tests/test_integrity.py::test_balance_consistency_and_reconciliation` |
| **Concurrent Debits** | Multi-threaded race test guarantees balance never negative | `tests/test_concurrency.py::test_concurrent_debit_prevents_overdraft` |
| **Concurrent Duplicates** | 5 simultaneous identical submissions allow only 1 | `tests/test_concurrency.py::test_concurrent_duplicate_reference_submission` |

---

## 📄 Documentation

For deep technical insights on row locking, monetary arithmetic, and concurrency trade-offs, see [docs/design-decisions.md](docs/design-decisions.md).
