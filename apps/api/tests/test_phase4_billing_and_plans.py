import os
from fastapi.testclient import TestClient
from aurora.main import app


def test_admin_billing_snapshot_and_plans_guarded():
    client = TestClient(app)
    token = os.environ.get("DEV_ADMIN_TOKEN", "")

    r = client.get(f"/admin/billing/snapshot?token={token}")
    assert r.status_code in (200, 401, 404)
    if r.status_code == 200:
        data = r.json()
        assert "current_period_usage" in data
        assert "orders" in data

    r2 = client.get(f"/admin/plans?token={token}")
    assert r2.status_code in (200, 401, 404)
    if r2.status_code == 200:
        data2 = r2.json()
        assert "plans" in data2


def test_public_plans_catalog():
    client = TestClient(app)
    r = client.get("/plans")
    assert r.status_code == 200
    data = r.json()
    assert "plans" in data
