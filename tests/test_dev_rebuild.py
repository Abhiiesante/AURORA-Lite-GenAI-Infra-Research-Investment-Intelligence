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


def test_dev_rebuild_comentions_requires_token(client: TestClient):
    r = client.post("/dev/graph/rebuild-comentions")
    assert r.status_code == 401


def test_dev_rebuild_comentions_ok_with_header(client: TestClient):
    r = client.post("/dev/graph/rebuild-comentions", headers={"X-Dev-Token": "test-admin-token"})
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
    assert "ok" in r.json()
