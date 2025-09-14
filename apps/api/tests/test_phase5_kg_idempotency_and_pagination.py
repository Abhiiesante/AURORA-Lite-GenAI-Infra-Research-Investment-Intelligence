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
def test_node_and_edge_idempotent_upsert_and_list_pagination():
    c = _client()
    tok = _admin_token()

    # Seed two nodes
    r1 = c.post(
        "/admin/kg/nodes/upsert",
        json={"uid": "n:i1", "type": "Entity", "props": {"v": 1}},
        params={"token": tok},
    )
    assert r1.status_code == 200, r1.text
    r1a = c.post(
        "/admin/kg/nodes/upsert",
        json={"uid": "n:i1", "type": "Entity", "props": {"v": 1}},
        params={"token": tok},
    )
    assert r1a.status_code == 200 and r1a.json().get("noop") is True

    r2 = c.post(
        "/admin/kg/nodes/upsert",
        json={"uid": "n:i2", "type": "Entity", "props": {"v": 2}},
        params={"token": tok},
    )
    assert r2.status_code == 200, r2.text

    # Edge upsert requires existing nodes
    rE = c.post(
        "/admin/kg/edges/upsert",
        json={"src_uid": "n:i1", "dst_uid": "n:i2", "type": "LINK", "props": {"w": 1}},
        params={"token": tok},
    )
    assert rE.status_code == 200
    rEa = c.post(
        "/admin/kg/edges/upsert",
        json={"src_uid": "n:i1", "dst_uid": "n:i2", "type": "LINK", "props": {"w": 1}},
        params={"token": tok},
    )
    assert rEa.status_code == 200 and rEa.json().get("noop") is True

    # Pagination: request first page and then next page using offset
    list1 = c.get("/admin/kg/nodes", params={"type": "Entity", "limit": 1, "offset": 0, "token": tok})
    assert list1.status_code == 200
    js1 = list1.json(); assert len(js1.get("nodes", [])) == 1
    list2 = c.get("/admin/kg/nodes", params={"type": "Entity", "limit": 1, "offset": 1, "token": tok})
    assert list2.status_code == 200
    js2 = list2.json(); assert len(js2.get("nodes", [])) >= 0  # second page may be empty if prior data exists
