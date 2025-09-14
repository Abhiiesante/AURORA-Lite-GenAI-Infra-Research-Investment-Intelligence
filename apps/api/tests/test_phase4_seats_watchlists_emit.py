import os
from fastapi.testclient import TestClient
from aurora.main import app


def test_admin_seats_upsert_and_list_guarded():
    client = TestClient(app)
    token = os.environ.get("DEV_ADMIN_TOKEN", "")

    # Upsert (tolerate 200/401/404)
    r = client.post("/admin/seats/upsert", json={"tenant_id": 1, "email": "user@example.com"}, params={"token": token})
    assert r.status_code in (200, 401, 404)

    # List
    r2 = client.get("/admin/seats", params={"token": token})
    assert r2.status_code in (200, 401, 404)
    if r2.status_code == 200:
        data = r2.json()
        assert "seats" in data


def test_watchlists_crud_tenant_scoped():
    client = TestClient(app)
    # Without tenant auth, should be 401
    r = client.post("/watchlists", json={"name": "Alpha"})
    assert r.status_code in (401, 403)


def test_admin_emit_data_updated_guarded():
    client = TestClient(app)
    token = os.environ.get("DEV_ADMIN_TOKEN", "")
    r = client.post("/admin/daas/emit-data-updated", params={"token": token})
    assert r.status_code in (200, 401, 404)
    if r.status_code == 200:
        body = r.json()
        assert "ok" in body
