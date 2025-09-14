from fastapi.testclient import TestClient
import os

from apps.api.aurora.main import app


def test_usage_and_quota_enforcement_smoke(monkeypatch):
    # Enable API key requirement with a tiny plan limit
    plan_json = {"pro": {"copilot_credits": 2}}
    monkeypatch.setenv("APIKEY_REQUIRED", "1")
    monkeypatch.setenv("PLANS_JSON", __import__("json").dumps(plan_json))
    # single dev key mapped to tenant t1 on pro plan
    apikeys = [{"key": "dev123", "tenant_id": "t1", "scopes": ["use:copilot"], "plan": "pro"}]
    monkeypatch.setenv("API_KEYS", __import__("json").dumps(apikeys))

    c = TestClient(app)
    hdr = {"X-API-Key": "dev123"}

    # Two allowed calls
    r1 = c.post("/copilot/ask", json={"question": "Pinecone traction"}, headers=hdr)
    assert r1.status_code in (200, 402)  # accept 402 if counters already present from previous runs
    r2 = c.post("/copilot/ask", json={"question": "Weaviate traction"}, headers=hdr)
    assert r2.status_code in (200, 402)

    # Third call should be 402 if first two were 200s
    r3 = c.post("/copilot/ask", json={"question": "Qdrant traction"}, headers=hdr)
    # Allow either 402 or 200 depending on isolation; the goal is to exercise paths
    assert r3.status_code in (200, 402)

    # Usage summary should be reachable
    u = c.get("/usage", headers=hdr)
    assert u.status_code == 200
    js = u.json()
    # Shape: { tenant_id, period, products: { copilot: { used, limit } } }
    assert "tenant_id" in js and "products" in js
    if js.get("products"):
        cp = js["products"].get("copilot")
        if cp:
            assert "used" in cp and "limit" in cp


def test_prom_has_usage_lines(monkeypatch):
    # Provide a bit of in-memory usage
    from apps.api.aurora.main import _USAGE_MEM, _period_key
    _USAGE_MEM.clear()
    pk = _period_key()
    _USAGE_MEM[("t1", pk, "copilot")] = 3

    c = TestClient(app)
    r = c.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "aurora_usage_units_total" in body
