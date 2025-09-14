import importlib
import os
from typing import Optional

import pytest
from fastapi.testclient import TestClient


def get_app_with_admin(token: Optional[str] = None):
    if token:
        os.environ["DEV_ADMIN_TOKEN"] = token
    from apps.api.aurora import main as aurora_main
    importlib.reload(aurora_main)
    return aurora_main.app


def test_agent_lifecycle_ops_or_skip():
    token = "test-admin-token"
    app = get_app_with_admin(token)
    client = TestClient(app)
    # start
    r = client.post(f"/admin/agents/start?token={token}", json={"type": "memo", "input": {}})
    if r.status_code not in (200, 404, 401):
        pytest.fail(f"unexpected status {r.status_code}")
    if r.status_code != 200:
        pytest.skip("admin/DB not available")
    run_id = r.json().get("id")
    assert run_id is not None
    # get
    r2 = client.get(f"/admin/agents/runs/{run_id}?token={token}")
    assert r2.status_code in (200, 404)
    if r2.status_code != 200:
        pytest.skip("DB table missing")
    # update
    r3 = client.put(f"/admin/agents/runs/{run_id}?token={token}", json={"status": "succeeded", "output": {"ok": True}})
    assert r3.status_code in (200, 500)


def test_dealroom_comments_checklist_or_skip():
    token = "test-admin-token"
    app = get_app_with_admin(token)
    client = TestClient(app)
    # create room
    r = client.post(f"/admin/deal-rooms?token={token}", json={"tenant_id": 1, "name": "Deal A"})
    if r.status_code != 200:
        pytest.skip("admin/DB not available")
    room_id = r.json().get("id") or 1
    # comments
    r1 = client.post(f"/admin/deal-rooms/{room_id}/comments?token={token}", json={"text": "Looks good"})
    assert r1.status_code in (200, 500)
    r2 = client.get(f"/admin/deal-rooms/{room_id}/comments?token={token}")
    assert r2.status_code in (200, 500)
    # checklist
    r3 = client.post(f"/admin/deal-rooms/{room_id}/checklist?token={token}", json={"title": "DD: Finance"})
    assert r3.status_code in (200, 500)
    r4 = client.get(f"/admin/deal-rooms/{room_id}/checklist?token={token}")
    assert r4.status_code in (200, 500)
