import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(ROOT)
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)


@pytest.fixture(autouse=True)
def set_dev_token_env(monkeypatch):
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "test-admin-token")
    monkeypatch.delenv("APIKEY_REQUIRED", raising=False)


@pytest.fixture()
def client():
    from apps.api.aurora.main import app  # type: ignore
    return TestClient(app)


def test_deal_room_export_requires_token(client: TestClient):
    r = client.get("/admin/deal-rooms/123/export")
    assert r.status_code == 401


def test_deal_room_export_csv_ok_with_header(client: TestClient):
    r = client.get("/admin/deal-rooms/123/export?format=csv", headers={"X-Dev-Token": "test-admin-token"})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/csv")
    # Should include CSV header even if empty rows
    assert isinstance(r.text, str)
    assert "," in r.text or "section" in r.text.lower()  # flexible check for header presence
