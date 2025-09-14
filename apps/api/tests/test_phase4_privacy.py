import os
from fastapi.testclient import TestClient
from aurora.main import app


def test_privacy_export_and_delete_ok():
    client = TestClient(app)
    r = client.get("/privacy/export", headers={"X-User-Email": "user@example.com"})
    assert r.status_code == 200
    data = r.json()
    assert "email" in data
    assert data.get("email") == "user@example.com"
    assert "copilot_sessions" in data
    assert "seats" in data

    r2 = client.delete("/privacy/delete", headers={"X-User-Email": "user@example.com"})
    assert r2.status_code == 200
    body = r2.json()
    assert "ok" in body
