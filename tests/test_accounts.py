import uuid
from fastapi.testclient import TestClient


def test_create_account_success(client: TestClient):
    response = client.post("/api/v1/accounts", json={"name": "Alice Cooper"})
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Alice Cooper"
    assert data["balance"] == "0.00"
    assert "created_at" in data
    # Ensure ID is a valid UUID
    uuid.UUID(data["id"])


def test_create_account_initial_balance_cannot_be_set_by_client(client: TestClient):
    # Pass balance in request body; schema should forbid or ignore and force 0.00
    response = client.post("/api/v1/accounts", json={"name": "Bob", "balance": "1000.00"})
    # Extra forbid raises 422
    assert response.status_code == 422


def test_create_account_rejects_missing_name(client: TestClient):
    response = client.post("/api/v1/accounts", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_account_rejects_whitespace_name(client: TestClient):
    response = client.post("/api/v1/accounts", json={"name": "   "})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_get_balance_success(client: TestClient):
    # 1. Create account
    create_res = client.post("/api/v1/accounts", json={"name": "Charlie"})
    assert create_res.status_code == 201
    account_id = create_res.json()["id"]

    # 2. Get balance
    res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert res.status_code == 200
    data = res.json()
    assert data["account_id"] == account_id
    assert data["balance"] == "0.00"


def test_get_balance_not_found(client: TestClient):
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/accounts/{fake_id}/balance")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "ACCOUNT_NOT_FOUND"
