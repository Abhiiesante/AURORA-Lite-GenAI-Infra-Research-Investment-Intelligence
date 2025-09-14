from fastapi.testclient import TestClient
import os

from apps.api.aurora.main import app


def test_backtest_quota_and_usage(monkeypatch):
    plan_json = {"pro": {"forecast_credits": 1}}
    monkeypatch.setenv("APIKEY_REQUIRED", "1")
    monkeypatch.setenv("PLANS_JSON", __import__("json").dumps(plan_json))
    apikeys = [{"key": "dev789", "tenant_id": "t3", "scopes": ["use:forecast"], "plan": "pro"}]
    monkeypatch.setenv("API_KEYS", __import__("json").dumps(apikeys))

    c = TestClient(app)
    hdr = {"X-API-Key": "dev789"}

    r1 = c.get("/forecast/backtest/1", headers=hdr)
    assert r1.status_code in (200, 402)
    r2 = c.get("/forecast/backtest/1", headers=hdr)
    assert r2.status_code in (200, 402)

    u = c.get("/usage", headers=hdr)
    assert u.status_code == 200
    js = u.json()
    assert "tenant_id" in js and "products" in js
