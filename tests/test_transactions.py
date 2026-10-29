import uuid
from fastapi.testclient import TestClient


def create_test_account(client: TestClient, name: str = "Test User") -> str:
    res = client.post("/api/v1/accounts", json={"name": name})
    assert res.status_code == 201
    return res.json()["id"]


def test_credit_transaction_updates_balance(client: TestClient):
    account_id = create_test_account(client, "Credit User")

    # Credit 100.00
    res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "100.00",
            "description": "Initial deposit",
            "reference_id": "DEP-001"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["account_id"] == account_id
    assert data["type"] == "credit"
    assert data["amount"] == "100.00"
    assert data["reference_id"] == "DEP-001"
    assert data["resulting_balance"] == "100.00"

    # Verify balance endpoint returns 100.00
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "100.00"


def test_debit_transaction_updates_balance(client: TestClient):
    account_id = create_test_account(client, "Debit User")

    # Credit 100.00 first
    client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "100.00",
            "description": "Deposit",
            "reference_id": "DEP-002"
        }
    )

    # Debit 30.00
    res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "type": "debit",
            "amount": "30.00",
            "description": "Book purchase",
            "reference_id": "PUR-001"
        }
    )
    assert res.status_code == 201
    assert res.json()["resulting_balance"] == "70.00"

    # Balance check
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "70.00"


def test_debit_insufficient_funds_rejected(client: TestClient):
    account_id = create_test_account(client, "Overdraft User")

    # Credit 100.00
    client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "100.00",
            "description": "Deposit",
            "reference_id": "DEP-003"
        }
    )

    # Debit 150.00 (exceeds balance 100)
    res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "type": "debit",
            "amount": "150.00",
            "description": "Overdraft attempt",
            "reference_id": "PUR-OVER"
        }
    )
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "INSUFFICIENT_FUNDS"

    # Balance remains 100.00
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "100.00"

    # Verify no transaction record was created
    history_res = client.get(f"/api/v1/accounts/{account_id}/transactions")
    assert history_res.json()["pagination"]["total_records"] == 1


def test_duplicate_reference_id_rejected(client: TestClient):
    account_id = create_test_account(client, "Duplicate User")

    # First transaction
    res1 = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "50.00",
            "description": "Payment",
            "reference_id": "REF-DUP-1"
        }
    )
    assert res1.status_code == 201

    # Second transaction with identical reference_id
    res2 = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "50.00",
            "description": "Repeat payment",
            "reference_id": "REF-DUP-1"
        }
    )
    assert res2.status_code == 409
    data = res2.json()
    assert data["error"]["code"] == "DUPLICATE_TRANSACTION"

    # Balance must remain 50.00 (not 100.00)
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "50.00"


def test_same_reference_id_allowed_on_different_accounts(client: TestClient):
    acc1 = create_test_account(client, "Acc 1")
    acc2 = create_test_account(client, "Acc 2")

    ref = "SHARED-REF-100"

    res1 = client.post(
        f"/api/v1/accounts/{acc1}/transactions",
        json={
            "type": "credit",
            "amount": "25.00",
            "description": "Deposit 1",
            "reference_id": ref
        }
    )
    assert res1.status_code == 201

    res2 = client.post(
        f"/api/v1/accounts/{acc2}/transactions",
        json={
            "type": "credit",
            "amount": "40.00",
            "description": "Deposit 2",
            "reference_id": ref
        }
    )
    assert res2.status_code == 201


def test_transaction_validation_errors(client: TestClient):
    account_id = create_test_account(client, "Val User")

    # 1. Zero amount
    res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"type": "credit", "amount": "0.00", "description": "Zero", "reference_id": "Z1"}
    )
    assert res.status_code == 422

    # 2. Negative amount
    res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"type": "credit", "amount": "-10.00", "description": "Negative", "reference_id": "N1"}
    )
    assert res.status_code == 422

    # 3. Excessive decimal precision (> 2 decimal places)
    res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"type": "credit", "amount": "10.123", "description": "Too precise", "reference_id": "P1"}
    )
    assert res.status_code == 422

    # 4. Invalid transaction type
    res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"type": "transfer", "amount": "10.00", "description": "Transfer", "reference_id": "T1"}
    )
    assert res.status_code == 422

    # 5. Non-existent account
    fake_id = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/accounts/{fake_id}/transactions",
        json={"type": "credit", "amount": "10.00", "description": "Ghost", "reference_id": "G1"}
    )
    assert res.status_code == 404
