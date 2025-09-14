from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_gate_status_includes_evals_pass(monkeypatch):
    client = TestClient(app)
    r = client.get("/dev/gates/status")
    assert r.status_code == 200
    data = r.json()
    assert "evals" in data
    ev = data.get("evals") or {}
    # Should include a boolean pass key computed against thresholds
    assert isinstance(ev.get("pass"), bool)


def test_forecast_per_metric_threshold_env(monkeypatch):
    client = TestClient(app)
    # Set a very strict threshold for a fake metric name to see threshold wiring
    monkeypatch.setenv("CI_FORECAST_METRIC", "mentions")
    monkeypatch.setenv("SMAPE_MAX_MENTIONS", "200")
    r = client.get("/dev/gates/status")
    assert r.status_code == 200
    gate = r.json().get("forecast")
    assert gate is not None
    # The threshold should reflect our override env
    assert float(gate.get("threshold")) == 200.0