import os
import time

import pytest

from fastapi.testclient import TestClient


pytestmark = pytest.mark.phase5


def _client(app_path="apps.api.aurora.main_shim"):
    import importlib

    mod = importlib.import_module(app_path)
    return TestClient(mod.app)


def _admin_token():
    return os.getenv("DEV_ADMIN_TOKEN")


@pytest.mark.skipif(not _admin_token(), reason="admin token not configured")
def test_kg_upsert_then_query_and_snapshot_hash_stable():
    c = _client()
    tok = _admin_token()
    # upsert two nodes and an edge
    r1 = c.post(
        "/admin/kg/nodes/upsert",
        json={"uid": "n:alpha", "type": "Company", "props": {"name": "Alpha"}},
        params={"token": tok},
    )
    assert r1.status_code == 200, r1.text

    r2 = c.post(
        "/admin/kg/nodes/upsert",
        json={"uid": "n:beta", "type": "Company", "props": {"name": "Beta"}},
        params={"token": tok},
    )
    assert r2.status_code == 200, r2.text

    r3 = c.post(
        "/admin/kg/edges/upsert",
        json={"src_uid": "n:alpha", "dst_uid": "n:beta", "type": "PARTNER"},
        params={"token": tok},
    )
    assert r3.status_code == 200, r3.text

    # the query should reflect at least one of the nodes
    q = c.post("/kg/query", json={"node": "n:alpha", "limit": 5})
    assert q.status_code == 200, q.text
    data = q.json()
    assert any(n.get("uid") == "n:alpha" for n in data.get("nodes", []))

    # snapshot twice; with stable state the hash should be identical
    s1 = c.post("/admin/kg/snapshot", params={"token": tok})
    assert s1.status_code == 200, s1.text
    h1 = s1.json().get("snapshot_hash")
    time.sleep(0.1)
    s2 = c.post("/admin/kg/snapshot", params={"token": tok})
    assert s2.status_code == 200, s2.text
    h2 = s2.json().get("snapshot_hash")
    assert h1 == h2
