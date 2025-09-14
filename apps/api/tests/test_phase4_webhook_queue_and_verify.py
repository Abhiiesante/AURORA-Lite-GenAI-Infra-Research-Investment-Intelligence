import os
import importlib
from typing import Optional

import pytest
from fastapi.testclient import TestClient


def _get_app(token: Optional[str] = None):
    if token:
        os.environ["DEV_ADMIN_TOKEN"] = token
    from apps.api.aurora import main as aurora_main
    importlib.reload(aurora_main)
    return aurora_main.app


def test_admin_webhook_queue_and_metric():
    token = "test-admin-token"
    app = _get_app(token)
    client = TestClient(app)

    # Metric presence (optional, skip if missing)
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    if "aurora_webhook_queue_depth" not in body:
        pytest.skip("webhook queue metric disabled")

    # Admin queue endpoint
    r2 = client.get(f"/admin/webhooks/queue?token={token}")
    if r2.status_code == 404:
        pytest.skip("admin queue endpoint not enabled")
    assert r2.status_code == 200
    data = r2.json()
    assert "depth" in data and "max_attempts" in data


def test_dev_webhooks_verify_signature():
    app = _get_app()
    client = TestClient(app)
    r = client.post("/dev/webhooks/verify", params={"secret": "s", "timestamp": "123", "body": "{}"})
    assert r.status_code == 200
    sig = r.json().get("signature")
    assert isinstance(sig, str) and len(sig) > 0
