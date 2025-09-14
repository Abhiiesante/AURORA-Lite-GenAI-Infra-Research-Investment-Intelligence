import os
import time

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.phase5


def _client():
    import importlib

    mod = importlib.import_module("apps.api.aurora.main_shim")
    return TestClient(mod.app)


def _admin_token():
    return os.getenv("DEV_ADMIN_TOKEN")


@pytest.mark.skipif(not _admin_token(), reason="admin token not configured")
def test_changed_feed_includes_recent_upserts():
    c = _client()
    tok = _admin_token()
    since = ("1970-01-01T00:00:00Z")

    # upsert a node and an edge
    c.post("/admin/kg/nodes/upsert", json={"uid": "n:cf-a", "type": "Entity"}, params={"token": tok})
    c.post("/admin/kg/nodes/upsert", json={"uid": "n:cf-b", "type": "Entity"}, params={"token": tok})
    c.post("/admin/kg/edges/upsert", json={"src_uid": "n:cf-a", "dst_uid": "n:cf-b", "type": "REL"}, params={"token": tok})

    time.sleep(0.05)
    r = c.get("/daas/kg/changed", params={"since": since, "limit": 50})
    assert r.status_code == 200
    js = r.json()
    nodes = js.get("nodes", [])
    edges = js.get("edges", [])
    assert any(n.get("uid") == "n:cf-a" for n in nodes)
    assert any(e.get("src") == "n:cf-a" and e.get("dst") == "n:cf-b" for e in edges)
