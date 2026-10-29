# LedgerFlow Architectural Design Decisions

This document details the engineering decisions, trade-offs, and invariants designed into the LedgerFlow transaction ledger system.

---

## 1. Zero Floating-Point Precision (`Decimal` & `NUMERIC(18,2)`)

### Decision
All monetary values (transaction amounts, balances, and ledger summaries) are strictly modeled using Python's `decimal.Decimal` and stored in PostgreSQL / relational storage as `NUMERIC(18, 2)`. Python `float` is prohibited across all schemas, service methods, and models.

### Rationale
IEEE 754 floating-point arithmetic introduces non-deterministic binary approximations (e.g. `0.1 + 0.2 = 0.30000000000000004`). In financial ledgers, fractional rounding drift creates cumulative discrepancies that violate double-entry auditing. `Decimal` guarantees exact base-10 arithmetic, deterministic two-decimal truncation, and immediate rejection of `NaN`, `Infinity`, and excessive fractional inputs (e.g. `10.555`).

---

## 2. Multi-Layer Concurrency Architecture & Row Locking

### Decision
Balance modifications are protected by a dual-layer concurrency mechanism:
1. **Pessimistic Row Locking (`SELECT ... FOR UPDATE`)**: In PostgreSQL, the target account row is locked before reading its balance or checking limits.
2. **Per-Account Mutex Synchronization (`threading.Lock`)**: In-process thread locks serialize requests within application workers and guarantee thread-safety during test suites and in-memory execution.

### Rationale
Without row locking, a classic "check-then-act" race condition occurs:
- Account balance is ₹100.00.
- Request 1 debits ₹80.00; Request 2 debits ₹80.00 simultaneously.
- Both threads concurrently read balance = ₹100.00, determine ₹100 >= ₹80 is valid, and proceed to deduct ₹80.00.
- Balance erroneously drops to -₹60.00 or creates a lost update.

With row locking, the first request locks the account row, decrements balance to ₹20.00, and commits. The second request only acquires the lock after commit, reads balance = ₹20.00, and is safely rejected with HTTP 422 (`INSUFFICIENT_FUNDS`). The balance never becomes negative.

---

## 3. Database-Level Unique Idempotency Constraint `(account_id, reference_id)`

### Decision
Idempotency and duplicate prevention are guaranteed by a composite unique constraint at the database table level:
```sql
CONSTRAINT uq_account_reference_id UNIQUE (account_id, reference_id)
```
In addition, the application performs an early duplicate lookup to return informative responses with existing transaction identifiers. Genuine race conditions that slip past the application check are caught by the database engine, rolled back, and translated into clean HTTP 409 (`DUPLICATE_TRANSACTION`) errors.

### Rationale
Application-level checks alone (`SELECT ... WHERE reference_id = ...`) are inherently vulnerable to concurrency races when two identical requests arrive within microseconds. The database unique constraint is the ultimate defense against duplicate posting and double-charging.

The same `reference_id` is allowed across different accounts (e.g. different users referencing their own invoice numbers), satisfying multi-tenant ledger requirements.

---

## 4. Single Atomic Unit of Work

### Decision
Both the insertion of the immutable `Transaction` record and the adjustment of `Account.balance` execute within the exact same database transaction boundary.

```python
db.add(transaction)
account.balance = new_balance
db.commit()
```

### Rationale
If balance updates and transaction logging were separate steps:
- A network timeout or server crash after inserting a transaction would leave the balance unchanged while the transaction exists.
- Conversely, updating the balance before logging could result in lost money without any audit trail.
By wrapping both actions into an atomic transaction, the ledger guarantees atomicity: both succeed together or both roll back completely.

---

## 5. Ledger Immutability

### Decision
There are no `PUT`, `PATCH`, or `DELETE` endpoints exposed for transactions. Once committed, a transaction record is permanent and unalterable.

### Rationale
Financial ledgers must maintain an append-only audit trail. If a mistake or correction occurs, real-world accounting systems do not overwrite history; they issue an offsetting credit or debit transaction. Modifying historical transaction records would invalidate historical reconciliations and compromise cryptographic auditing.

---

## 6. Deterministic Pagination & Database-Level Sorting

### Decision
Transaction history queries implement database-level `LIMIT` and `OFFSET` sorting by `created_at DESC, id DESC`. Filtering by transaction type (`credit` or `debit`) is applied before count evaluation and pagination slicing.

### Rationale
1. **Performance**: Querying with database-level pagination ensures memory consumption remains $O(limit)$ rather than loading thousands of records into Python memory.
2. **Determinism**: Because multiple transactions can share the exact same microsecond timestamp, sorting strictly by `created_at DESC` can lead to unstable page pagination (items shifting between pages). Adding the secondary key `id DESC` guarantees predictable, reproducible pagination across all requests.

---

## 7. Balance Reconciliation Diagnostic

### Decision
A dedicated read-only endpoint `GET /api/v1/accounts/{account_id}/reconciliation` audits the stored account balance against the ledger formula:
$$\text{Calculated Balance} = \sum \text{Credits} - \sum \text{Debits}$$

### Rationale
Provides automated verification that the materialized balance cached on the `Account` table has not drifted from the underlying transaction journal. It runs as a read-only audit check that does not alter data.
