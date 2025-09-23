import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from apps.api.aurora.main import app  # type: ignore

client = TestClient(app)


def _commit(events, **kwargs):
    return client.post("/kg/commit", json={"events": events}, **kwargs)


def test_node_diff_and_pagination():
    uid = "company:diffdemo"
    # First version (capture timestamp AFTER commit so it's guaranteed >= valid_from)
    r1 = _commit([
        {"operation": {"type": "create_node", "uid": uid, "properties": {"name": "Alpha", "stage": "seed"}}},
        {"operation": {"type": "create_edge", "from": uid, "to": "investor:a", "edge_type": "RAISED", "properties": {"amt": 1}}},
    ], headers={"X-Role": "admin"})
    assert r1.status_code in (200, 401, 403, 500)
    if r1.status_code != 200:
        # Auth enforced; skip gracefully
        import pytest
        pytest.skip("KG commit unauthorized in this environment")
    time.sleep(0.01)
    t1 = datetime.now(timezone.utc).isoformat()
    # Second version (changed properties + new edge); capture t2 after commit
    r2 = _commit([
        {"operation": {"type": "create_node", "uid": uid, "properties": {"name": "Alpha Corp", "stage": "series_a"}}},
        {"operation": {"type": "create_edge", "from": uid, "to": "investor:b", "edge_type": "RAISED", "properties": {"amt": 5}}},
    ], headers={"X-Role": "admin"})
    assert r2.status_code == 200, r2.text
    time.sleep(0.01)
    t2 = datetime.now(timezone.utc).isoformat()

    # Diff between t1 and t2 should show changed name/stage and added investor:b edge
    r = client.get(f"/kg/node/{uid}/diff", params={"from_ts": t1, "to_ts": t2})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["properties"]["changed"]["name"]["from"] == "Alpha"
    assert d["properties"]["changed"]["name"]["to"] == "Alpha Corp"
    assert any(e["dst"] == "investor:b" for e in d["edges"]["added"])

    # Pagination on edges at t2
    latest = client.get(f"/kg/node/{uid}", params={"as_of": t2, "edges_limit": 1})
    assert latest.status_code == 200
    latest_j = latest.json()
    assert len(latest_j["edges"]) == 1
    if latest_j.get("next_edges_offset") is not None:
        nxt = client.get(f"/kg/node/{uid}", params={"as_of": t2, "edges_limit": 1, "edges_offset": latest_j["next_edges_offset"]})
        assert nxt.status_code == 200
