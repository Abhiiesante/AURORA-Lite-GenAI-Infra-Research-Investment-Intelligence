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


def test_plan_crud_happy_path(client: TestClient):
    headers = {"X-Dev-Token": "test-admin-token"}

    # Create
    body = {"code": "test_basic", "entitlements": {"period": "monthly", "limits": {"foo": 1}}}
    r = client.post("/admin/plans", json=body, headers=headers)
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # Update
    body_update = {"code": "test_basic", "entitlements": {"period": "monthly", "limits": {"foo": 2}}}
    r = client.put("/admin/plans/test_basic", json=body_update, headers=headers)
    assert r.status_code == 200
    assert r.json().get("ok") is True

    # Delete
    r = client.delete("/admin/plans/test_basic", headers=headers)
    assert r.status_code == 200
    assert r.json().get("ok") is True
