import uuid
import pytest
from fastapi.testclient import TestClient


def create_account_with_transactions(client: TestClient) -> str:
    res = client.post("/api/v1/accounts", json={"name": "History User"})
    account_id = res.json()["id"]

    # Add 3 credits and 2 debits
    transactions = [
        {"type": "credit", "amount": "100.00", "description": "Deposit 1", "reference_id": "H-1"},
        {"type": "credit", "amount": "50.00", "description": "Deposit 2", "reference_id": "H-2"},
        {"type": "debit", "amount": "20.00", "description": "Expense 1", "reference_id": "H-3"},
        {"type": "credit", "amount": "30.00", "description": "Deposit 3", "reference_id": "H-4"},
        {"type": "debit", "amount": "10.00", "description": "Expense 2", "reference_id": "H-5"},
    ]

    for tx in transactions:
        res_tx = client.post(f"/api/v1/accounts/{account_id}/transactions", json=tx)
        assert res_tx.status_code == 201

    return account_id


def test_get_history_all_sorted_newest_first(client: TestClient):
    account_id = create_account_with_transactions(client)

    res = client.get(f"/api/v1/accounts/{account_id}/transactions")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 5
    assert data["pagination"]["total_records"] == 5
    assert data["pagination"]["total_pages"] == 1

    # Verify latest first order: H-5 was posted last, so it should be first
    assert data["items"][0]["reference_id"] == "H-5"
    assert data["items"][-1]["reference_id"] == "H-1"


def test_filter_by_type_credit(client: TestClient):
    account_id = create_account_with_transactions(client)

    res = client.get(f"/api/v1/accounts/{account_id}/transactions?type=credit")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 3
    assert data["pagination"]["total_records"] == 3
    assert all(item["type"] == "credit" for item in data["items"])


def test_filter_by_type_debit(client: TestClient):
    account_id = create_account_with_transactions(client)

    res = client.get(f"/api/v1/accounts/{account_id}/transactions?type=debit")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["pagination"]["total_records"] == 2
    assert all(item["type"] == "debit" for item in data["items"])


def test_pagination_pages_and_limits(client: TestClient):
    account_id = create_account_with_transactions(client)

    # Page 1, limit 2
    res_p1 = client.get(f"/api/v1/accounts/{account_id}/transactions?page=1&limit=2")
    assert res_p1.status_code == 200
    p1 = res_p1.json()
    assert len(p1["items"]) == 2
    assert p1["pagination"]["page"] == 1
    assert p1["pagination"]["limit"] == 2
    assert p1["pagination"]["total_records"] == 5
    assert p1["pagination"]["total_pages"] == 3
    assert p1["items"][0]["reference_id"] == "H-5"
    assert p1["items"][1]["reference_id"] == "H-4"

    # Page 2, limit 2
    res_p2 = client.get(f"/api/v1/accounts/{account_id}/transactions?page=2&limit=2")
    assert res_p2.status_code == 200
    p2 = res_p2.json()
    assert len(p2["items"]) == 2
    assert p2["pagination"]["page"] == 2
    assert p2["items"][0]["reference_id"] == "H-3"
    assert p2["items"][1]["reference_id"] == "H-2"

    # Page 3, limit 2
    res_p3 = client.get(f"/api/v1/accounts/{account_id}/transactions?page=3&limit=2")
    assert res_p3.status_code == 200
    p3 = res_p3.json()
    assert len(p3["items"]) == 1
    assert p3["items"][0]["reference_id"] == "H-1"


def test_empty_page_when_no_records(client: TestClient):
    res = client.post("/api/v1/accounts", json={"name": "Empty User"})
    account_id = res.json()["id"]

    res_history = client.get(f"/api/v1/accounts/{account_id}/transactions")
    assert res_history.status_code == 200
    data = res_history.json()
    assert data["items"] == []
    assert data["pagination"]["total_records"] == 0
    assert data["pagination"]["total_pages"] == 0


def test_history_invalid_account_returns_404(client: TestClient):
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/accounts/{fake_id}/transactions")
    assert res.status_code == 404
