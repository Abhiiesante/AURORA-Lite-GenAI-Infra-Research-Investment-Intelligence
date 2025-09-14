from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_forecast_backtest_shape_and_bounds():
    c = TestClient(app)
    r = c.get("/forecast/backtest/1", params={"metric": "mentions"})
    assert r.status_code == 200
    data = r.json()
    assert {"company", "metric", "n", "smape"}.issubset(data.keys())
    assert isinstance(data["n"], int) and data["n"] >= 0
    # SMAPE is between 0 and 200 by definition here
    smape = float(data["smape"])
    assert 0.0 <= smape <= 200.0
