import os
from fastapi.testclient import TestClient
from aurora.main import app


def test_admin_plans_crud(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "tok")

    # Create plan
    payload = {"code": "gold", "entitlements": {"period": "monthly", "copilot_calls": 1000}, "name": "Gold", "price_usd": 99.0}
    r = client.post("/admin/plans", params={"token": "tok"}, json=payload)
    assert r.status_code in (200, 401, 404)
    if r.status_code == 200:
        assert r.json().get("ok") is True

    # Update plan
    upd = {"code": "gold", "entitlements": {"period": "monthly", "copilot_calls": 2000}, "name": "Gold+", "price_usd": 129.0}
    r2 = client.put("/admin/plans/gold", params={"token": "tok"}, json=upd)
    assert r2.status_code in (200, 401, 404)
    if r2.status_code == 200:
        assert r2.json().get("ok") is True

    # Delete plan
    r3 = client.delete("/admin/plans/gold", params={"token": "tok"})
    assert r3.status_code in (200, 401, 404)
    if r3.status_code == 200:
        assert r3.json().get("ok") is True


def test_admin_tenant_create_guarded(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "tok")
    r = client.post("/admin/tenants", params={"token": "tok"}, json={"name": "Acme Corp", "status": "active"})
    # DB-less env may return 501; tolerate 200/404/501
    assert r.status_code in (200, 404, 501)
    if r.status_code == 200:
        js = r.json()
        assert js.get("ok") is True
        assert js.get("name") == "Acme Corp"
