from fastapi.testclient import TestClient

from apps.api.aurora.main import app


client = TestClient(app)


def test_market_perf_gate_contract():
    r = client.get("/dev/gates/market-perf")
    assert r.status_code == 200
    data = r.json()
    for k in ("p95_ms", "budget_ms", "samples", "size", "pass"):
        assert k in data


def test_gate_status_includes_market():
    r = client.get("/dev/gates/status")
    assert r.status_code == 200
    data = r.json()
    assert "market" in data and isinstance(data["market"], dict)
    assert "pass" in data["market"]