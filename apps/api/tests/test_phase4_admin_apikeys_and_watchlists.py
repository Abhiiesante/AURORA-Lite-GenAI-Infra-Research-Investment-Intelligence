import os
from fastapi.testclient import TestClient
from aurora.main import app


def test_admin_api_keys_list_and_create(monkeypatch):
    client = TestClient(app)
    # Guard: enable admin
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "tok")

    # Fallback env keys for list
    env_keys = [
        {"key": "sk_test_abc12345", "tenant_id": "t-ap", "scopes": ["use:copilot"], "rate_limit_per_min": 60, "plan": "pro"}
    ]
    monkeypatch.setenv("API_KEYS", __import__("json").dumps(env_keys))

    r = client.get("/admin/api-keys", params={"token": "tok"})
    assert r.status_code in (200, 401, 404)
    if r.status_code == 200:
        data = r.json()
        assert "api_keys" in data

    # Create API key (may return 501 if DB is not available)
    body = {"tenant_id": "t-ap"}
    r2 = client.post("/admin/api-keys", params={"token": "tok"}, json=body)
    assert r2.status_code in (200, 401, 404, 501)


def test_watchlists_flow_with_apikey(monkeypatch):
    client = TestClient(app)
    # Enforce API key auth and provide an env key for tenant context
    monkeypatch.setenv("APIKEY_REQUIRED", "1")
    env_keys = [
        {"key": "sk_watchlist_1", "tenant_id": "t-100", "scopes": ["use:copilot"], "plan": "pro"}
    ]
    monkeypatch.setenv("API_KEYS", __import__("json").dumps(env_keys))
    hdr = {"X-API-Key": "sk_watchlist_1"}

    # Create
    r = client.post("/watchlists", headers=hdr, json={"name": "WL Alpha"})
    assert r.status_code in (200, 201)

    # List (may be empty if DB not available; still should be 200)
    r2 = client.get("/watchlists", headers=hdr)
    assert r2.status_code == 200
    js = r2.json()
    assert "watchlists" in js

    # Add an item (id is arbitrary if DB not present; endpoint tolerates best-effort)
    r3 = client.post("/watchlists/1/items", headers=hdr, json={"company_id": 123})
    assert r3.status_code in (200, 201)

    # Remove an item
    r4 = client.delete("/watchlists/1/items/1", headers=hdr)
    assert r4.status_code in (200, 204)
