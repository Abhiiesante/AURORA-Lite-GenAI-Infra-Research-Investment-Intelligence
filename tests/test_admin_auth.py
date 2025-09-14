import os
import sys
from typing import Optional

import pytest
from fastapi.testclient import TestClient

# Ensure project root on path
ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(ROOT)
if PROJ not in sys.path:
    sys.path.insert(0, PROJ)


@pytest.fixture(autouse=True)
def set_dev_token_env(monkeypatch):
    # Set a known admin token for tests
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "test-admin-token")
    # Ensure apikey is not enforced globally for admin routes during this test
    monkeypatch.delenv("APIKEY_REQUIRED", raising=False)


@pytest.fixture()
def client():
    # Import app after env is set to pick up settings
    from apps.api.aurora.main import app  # type: ignore
    return TestClient(app)


def test_admin_plans_requires_token(client: TestClient):
    # No token -> 401 (since token is configured)
    r = client.get("/admin/plans")
    assert r.status_code == 401


def test_admin_plans_accepts_header_token(client: TestClient):
    r = client.get("/admin/plans", headers={"X-Dev-Token": "test-admin-token"})
    assert r.status_code == 200
    assert "plans" in r.json()


def test_admin_plans_accepts_query_token(client: TestClient):
    r = client.get("/admin/plans?token=test-admin-token")
    assert r.status_code == 200
    assert "plans" in r.json()


def test_admin_plans_rejects_wrong_token(client: TestClient):
    r = client.get("/admin/plans", headers={"X-Dev-Token": "wrong"})
    assert r.status_code == 401
