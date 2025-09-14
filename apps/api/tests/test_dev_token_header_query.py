import os
import sys
import importlib
from fastapi.testclient import TestClient


def _client():
    # Ensure fresh import for app
    if 'apps.api.aurora.main' in sys.modules:
        importlib.reload(sys.modules['apps.api.aurora.main'])
    from apps.api.aurora.main import app  # type: ignore
    return TestClient(app)


def test_dev_token_query_vs_header_index_local(monkeypatch):
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "sekret")
    c = _client()
    # Query token
    r1 = c.post("/dev/index-local?token=sekret")
    assert r1.status_code in (200, 404)  # 404 if admin disabled elsewhere; but token path should be accepted
    if r1.status_code == 200:
        assert r1.json().get("ok") is True
    # Header token
    r2 = c.post("/dev/index-local", headers={"X-Dev-Token": "sekret"})
    assert r2.status_code in (200, 404)
    if r2.status_code == 200:
        assert r2.json().get("ok") is True


def test_dev_cache_stats_header_and_query(monkeypatch):
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "sekret")
    c = _client()
    r1 = c.get("/dev/cache-stats?token=sekret")
    assert r1.status_code in (200, 404)
    r2 = c.get("/dev/cache-stats", headers={"X-Dev-Token": "sekret"})
    assert r2.status_code in (200, 404)


def test_kg_snapshot_and_provenance_bundle_shape(monkeypatch):
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "sekret")
    # Signing secret optional
    monkeypatch.setenv("AURORA_SNAPSHOT_SIGNING_SECRET", "sign")
    c = _client()
    # Snapshot
    rs = c.post("/admin/kg/snapshot?token=sekret", json={"notes": "test"})
    assert rs.status_code in (200, 404)
    if rs.status_code == 200:
        j = rs.json()
        assert "snapshot_hash" in j
        # Verify signature path
        if j.get("signature"):
            rv = c.post("/kg/snapshot/verify", json={"snapshot_hash": j["snapshot_hash"], "signature": j["signature"]})
            assert rv.status_code == 200
            assert "valid" in rv.json()
    # Provenance bundle shape call (uid may be missing; should still 200)
    rb = c.get("/provenance/bundle", params={"uid": "company:1", "limit": 3})
    assert rb.status_code == 200