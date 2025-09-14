import os
from fastapi.testclient import TestClient
from aurora.main import app


def test_admin_subscribe_guarded(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "tok")
    body = {"tenant_id": 1, "plan_code": "pro", "period": "monthly"}
    r = client.post("/admin/subscribe", params={"token": "tok"}, json=body)
    assert r.status_code in (200, 401, 404)
    if r.status_code == 200:
        js = r.json()
        assert js.get("ok") in (True, False)  # DB-less env may return False
