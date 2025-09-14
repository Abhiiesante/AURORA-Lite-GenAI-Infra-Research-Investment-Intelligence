from fastapi.testclient import TestClient
import aurora.main as main

def test_perf_ego_endpoint_shape(monkeypatch):
    # Allow startup without DB
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.get("/dev/perf/ego-check?depth=2&limit=500&runs=3&target_p95_ms=2000")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    stats = data.get("stats") or {}
    assert "runs" in stats and "p95_ms" in stats and "pass" in stats
