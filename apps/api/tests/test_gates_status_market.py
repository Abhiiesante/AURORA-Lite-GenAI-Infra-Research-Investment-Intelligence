from fastapi.testclient import TestClient
from aurora.main import app

def test_gate_status_non_strict_works():
    c = TestClient(app)
    r = c.get('/dev/gates/status?strict=false')
    assert r.status_code == 200
    data = r.json()
    assert set(['perf','forecast','errors','rag','market','thresholds','pass']).issubset(data.keys())


def test_gate_market_perf_smoke():
    c = TestClient(app)
    r = c.get('/dev/gates/market-perf?size=50&runs=3')
    assert r.status_code == 200
    d = r.json()
    assert 'p95_ms' in d and 'budget_ms' in d and 'pass' in d
