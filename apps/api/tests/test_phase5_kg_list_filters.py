import os

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
def test_list_nodes_and_edges_filters():
    c = _client()
    tok = _admin_token()

    # seed a tiny graph
    c.post("/admin/kg/nodes/upsert", json={"uid": "n:x", "type": "Person", "props": {"n": 1}}, params={"token": tok})
    c.post("/admin/kg/nodes/upsert", json={"uid": "n:y", "type": "Person", "props": {"n": 2}}, params={"token": tok})
    c.post("/admin/kg/edges/upsert", json={"src_uid": "n:x", "dst_uid": "n:y", "type": "KNOWS"}, params={"token": tok})

    # list nodes by type
    r = c.get("/admin/kg/nodes", params={"type": "Person", "limit": 10, "token": tok})
    assert r.status_code == 200
    js = r.json()
    assert len(js.get("nodes", [])) >= 2
    assert all(n["type"] == "Person" for n in js["nodes"])  # type filter applied

    # list edges with src filter
    r2 = c.get("/admin/kg/edges", params={"src_uid": "n:x", "limit": 10, "token": tok})
    assert r2.status_code == 200
    js2 = r2.json()
    assert any(e["src_uid"] == "n:x" for e in js2.get("edges", []))
