from fastapi.testclient import TestClient


def test_balance_consistency_and_reconciliation(client: TestClient):
    # Create account
    create_res = client.post("/api/v1/accounts", json={"name": "Audit User"})
    account_id = create_res.json()["id"]

    # Initial balance: 0
    assert create_res.json()["balance"] == "0.00"

    # Operations from assessment specification:
    # Credit 100, Credit 50, Debit 30, Debit 20 -> Expected 100
    txs = [
        ("credit", "100.00", "REF-INT-1"),
        ("credit", "50.00", "REF-INT-2"),
        ("debit", "30.00", "REF-INT-3"),
        ("debit", "20.00", "REF-INT-4"),
    ]

    for tx_type, amount, ref in txs:
        post_res = client.post(
            f"/api/v1/accounts/{account_id}/transactions",
            json={"type": tx_type, "amount": amount, "description": f"Step {ref}", "reference_id": ref}
        )
        assert post_res.status_code == 201

    # Check final stored balance
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "100.00"

    # Run reconciliation service
    audit_res = client.get(f"/api/v1/accounts/{account_id}/reconciliation")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["is_consistent"] is True
    assert audit_data["stored_balance"] == "100.00"
    assert audit_data["calculated_balance"] == "100.00"
    assert audit_data["total_credits"] == "150.00"
    assert audit_data["total_debits"] == "50.00"
    assert audit_data["transaction_count"] == 4


def test_transaction_immutability_no_update_or_delete_routes(client: TestClient):
    create_res = client.post("/api/v1/accounts", json={"name": "Immutable User"})
    account_id = create_res.json()["id"]

    tx_res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"type": "credit", "amount": "100.00", "description": "Deposit", "reference_id": "REF-IMMUTABLE-1"}
    )
    tx_id = tx_res.json()["id"]

    # Try PUT / PATCH / DELETE on transactions endpoint
    put_res = client.put(f"/api/v1/accounts/{account_id}/transactions/{tx_id}", json={"amount": "200.00"})
    assert put_res.status_code in (404, 405)

    patch_res = client.patch(f"/api/v1/accounts/{account_id}/transactions/{tx_id}", json={"amount": "200.00"})
    assert patch_res.status_code in (404, 405)

    delete_res = client.delete(f"/api/v1/accounts/{account_id}/transactions/{tx_id}")
    assert delete_res.status_code in (404, 405)
