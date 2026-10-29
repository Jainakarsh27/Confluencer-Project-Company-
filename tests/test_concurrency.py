import concurrent.futures
from fastapi.testclient import TestClient


def test_concurrent_debit_prevents_overdraft(client: TestClient):
    """
    Ensure two simultaneous debits that together exceed the balance cannot both succeed.
    Starting balance: 100.00
    Debit A: 80.00
    Debit B: 80.00
    Result: Exactly one succeeds, one rejected with 422. Balance remains 20.00.
    """
    create_res = client.post("/api/v1/accounts", json={"name": "Race User"})
    account_id = create_res.json()["id"]

    # Deposit 100.00
    dep_res = client.post(
        f"/api/v1/accounts/{account_id}/transactions",
        json={"type": "credit", "amount": "100.00", "description": "Deposit", "reference_id": "INIT-100"}
    )
    assert dep_res.status_code == 201

    def send_debit(ref_suffix: str):
        return client.post(
            f"/api/v1/accounts/{account_id}/transactions",
            json={
                "type": "debit",
                "amount": "80.00",
                "description": f"Debit attempt {ref_suffix}",
                "reference_id": f"DEBIT-{ref_suffix}"
            }
        )

    # Launch concurrently in 2 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(send_debit, "A")
        f2 = executor.submit(send_debit, "B")
        res1 = f1.result()
        res2 = f2.result()

    status_codes = [res1.status_code, res2.status_code]
    assert 201 in status_codes, f"At least one debit should succeed: {status_codes}"
    assert 422 in status_codes, f"The second debit should be rejected: {status_codes}"

    # Balance must never be negative
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    final_balance = bal_res.json()["balance"]
    assert final_balance == "20.00", f"Expected balance 20.00, got {final_balance}"


def test_concurrent_duplicate_reference_submission(client: TestClient):
    """
    Simultaneously submit 5 identical transactions with the same account and reference_id.
    Exactly one must succeed (201), the rest must fail with 409 (DUPLICATE_TRANSACTION).
    """
    create_res = client.post("/api/v1/accounts", json={"name": "Duplicate Race User"})
    account_id = create_res.json()["id"]

    ref_id = "RACE-DUP-REF"

    def send_tx():
        return client.post(
            f"/api/v1/accounts/{account_id}/transactions",
            json={
                "type": "credit",
                "amount": "50.00",
                "description": "Concurrent deposit",
                "reference_id": ref_id
            }
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_tx) for _ in range(5)]
        responses = [f.result() for f in futures]

    statuses = [r.status_code for r in responses]
    success_count = statuses.count(201)
    conflict_count = statuses.count(409)

    assert success_count == 1, f"Expected exactly 1 success (201), got {success_count} ({statuses})"
    assert conflict_count == 4, f"Expected 4 conflicts (409), got {conflict_count} ({statuses})"

    # Final balance must be 50.00, NOT 250.00
    bal_res = client.get(f"/api/v1/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "50.00"
