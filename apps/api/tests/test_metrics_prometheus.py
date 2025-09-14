from fastapi.testclient import TestClient
from aurora.main import app

def test_metrics_exposes_help_and_gauges():
    c = TestClient(app)
    r = c.get('/metrics')
    assert r.status_code == 200
    txt = r.text
    # Basic HELP/TYPE lines present
    assert '# HELP aurora_hybrid_cache_hits' in txt
    assert '# TYPE aurora_requests_total' in txt
    # Has percentile gauges lines or at least one request metric line
    assert 'aurora_request_latency_avg_ms' in txt
    # Evals lines are best-effort; ensure endpoint is not empty
    assert len(txt.splitlines()) > 5
