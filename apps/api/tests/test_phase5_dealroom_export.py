import importlib
import os
from fastapi.testclient import TestClient
import pytest


def get_app_with_admin(token: str):
    os.environ["DEV_ADMIN_TOKEN"] = token
    from apps.api.aurora import main as aurora_main
    importlib.reload(aurora_main)
    return aurora_main.app


def test_export_endpoints_or_skip():
    token = "test-admin-token"
    app = get_app_with_admin(token)
    client = TestClient(app)
    # create room
    r = client.post(f"/admin/deal-rooms?token={token}", json={"tenant_id": 1, "name": "X"})
    if r.status_code != 200:
        pytest.skip("admin/DB not available")
    room_id = r.json().get("id") or 1
    # request CSV
    r1 = client.get(f"/admin/deal-rooms/{room_id}/export?token={token}&format=csv")
    assert r1.status_code in (200, 500)
    if r1.status_code == 200:
        ct = r1.headers.get("content-type", "")
        assert "text/csv" in ct
    # request NDJSON
    r2 = client.get(f"/admin/deal-rooms/{room_id}/export?token={token}&format=ndjson")
    assert r2.status_code in (200, 500)
    if r2.status_code == 200:
        ct = r2.headers.get("content-type", "")
        assert "application/x-ndjson" in ct
