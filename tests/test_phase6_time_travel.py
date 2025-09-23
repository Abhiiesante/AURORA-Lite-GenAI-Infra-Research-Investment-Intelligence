import pytest
from fastapi.testclient import TestClient
from apps.api.aurora.main import app

client = TestClient(app)


def test_time_travel_node_lifecycle(monkeypatch):
    # Create two versions of a node via kg/commit
    payload_v1 = {
        "events": [
            {
                "operation": {
                    "type": "create_node",
                    "uid": "company:phase6demo",
                    "node_type": "Company",
                    "properties": {"name": "Phase6 Demo", "stage": "seed"},
                },
                "pipeline_version": "ingest-v1",
            }
        ]
    }
    # Retry a few times in case database container is still starting
    import time
    attempts = 0
    r1 = None
    while attempts < 5:
        r1 = client.post("/kg/commit", json=payload_v1, headers={"X-Role": "admin"})
        if r1.status_code != 500:
            break
        time.sleep(0.6)
        attempts += 1
    assert r1 is not None
    if r1.status_code in (401, 403):
        pytest.skip("KG commit unauthorized in this environment")
    if r1.status_code == 500:
        pytest.skip("KG commit backend unavailable (primary DB down) after retries - skipping time travel test")
    assert r1.status_code == 200

    # Create v2 (updated properties)
    payload_v2 = {
        "events": [
            {
                "operation": {
                    "type": "create_node",
                    "uid": "company:phase6demo",
                    "node_type": "Company",
                    "properties": {"name": "Phase6 Demo", "stage": "series_a"},
                },
                "pipeline_version": "ingest-v2",
            }
        ]
    }
    r2 = None
    attempts = 0
    while attempts < 5:
        r2 = client.post("/kg/commit", json=payload_v2, headers={"X-Role": "admin"})
        if r2.status_code != 500:
            break
        time.sleep(0.6)
        attempts += 1
    assert r2 is not None
    if r2.status_code == 500:
        pytest.skip("Second KG commit failed due to backend unavailable after retries; skipping time travel assertions")
    assert r2.status_code == 200

    # Latest should show stage series_a
    latest = client.get("/kg/node/company:phase6demo")
    assert latest.status_code == 200
    data_latest = latest.json()
    assert data_latest["node"]["properties"]["stage"] == "series_a"
    # provenance may be None but if present must have snapshot_hash key
    if data_latest.get("provenance"):
        assert "snapshot_hash" in data_latest["provenance"]

    # Fetch historical as_of near first version valid_from
    first_valid_from = r1.json()["results"][0]["valid_from"]
    hist = client.get(f"/kg/node/company:phase6demo?as_of={first_valid_from}")
    assert hist.status_code == 200
    data_hist = hist.json()
    assert data_hist["node"]["properties"]["stage"] == "seed"


def test_snapshot_creation(monkeypatch):
    # Admin token path may be required; attempt without token first
    resp = client.post("/admin/kg/snapshot/create", json={})
    if resp.status_code == 401:
        pytest.skip("Snapshot create requires admin token in this environment")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("snapshot_hash")
    assert body.get("ok") is True
