from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_deals_sourcing_shape():
    c = TestClient(app)
    r = c.get("/deals/sourcing", params={"limit": 5})
    assert r.status_code == 200
    data = r.json()
    assert "deals" in data and isinstance(data["deals"], list)
    if data["deals"]:
        first = data["deals"][0]
        assert {"company_id", "name", "score"}.issubset(first.keys())


def test_forecast_shape():
    c = TestClient(app)
    r = c.get("/forecast/1", params={"metric": "mentions", "horizon": 4})
    assert r.status_code == 200
    data = r.json()
    assert "forecast" in data and isinstance(data["forecast"], list)
    if data["forecast"]:
        f0 = data["forecast"][0]
        assert {"date", "metric", "yhat", "yhat_lower", "yhat_upper"}.issubset(f0.keys())
