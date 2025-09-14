from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_dev_metrics_shape():
    client = TestClient(app)
    r = client.get("/dev/metrics")
    assert r.status_code in (200, 401)
    if r.status_code == 200:
        data = r.json()
        assert set(["request_count", "avg_latency_ms", "hybrid_cache", "timestamp"]).issubset(data.keys())
        assert set(["size", "hits", "misses"]).issubset(data["hybrid_cache"].keys())
