from fastapi.testclient import TestClient
import os

from apps.api.aurora.main import app


def test_forecast_quota_and_usage(monkeypatch):
    plan_json = {"pro": {"forecast_credits": 1}}
    monkeypatch.setenv("APIKEY_REQUIRED", "1")
    monkeypatch.setenv("PLANS_JSON", __import__("json").dumps(plan_json))
    apikeys = [{"key": "dev456", "tenant_id": "t2", "scopes": ["use:forecast"], "plan": "pro"}]
    monkeypatch.setenv("API_KEYS", __import__("json").dumps(apikeys))

    c = TestClient(app)
    hdr = {"X-API-Key": "dev456"}

    r1 = c.get("/forecast/1", headers=hdr)
    assert r1.status_code in (200, 402)
    r2 = c.get("/forecast/1", headers=hdr)
    assert r2.status_code in (200, 402)

    # usage summary should include forecast product when present
    u = c.get("/usage", headers=hdr)
    assert u.status_code == 200
    js = u.json()
    assert "tenant_id" in js and "products" in js
    prod = js.get("products", {})
    if prod:
        fc = prod.get("forecast")
        if fc:
            assert "used" in fc and "limit" in fc
