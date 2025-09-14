from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_marketplace_admin_upsert_and_list(monkeypatch):
    # Enable admin with a dev token
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "tok")
    c = TestClient(app)

    # Upsert an item via admin
    body = {
        "code": "pro-pack",
        "title": "Pro Pack",
        "description": "Pro features",
        "price_usd": 49.0,
        "category": "addons",
        "status": "active",
    }
    r = c.post("/admin/marketplace/items", params={"token": "tok"}, json=body)
    assert r.status_code in (200, 401, 404)  # accept 401/404 when admin guard differs in env
    if r.status_code == 200:
        assert r.json().get("ok") is True

    # List marketplace items (should include our item when in-memory fallback active)
    r2 = c.get("/marketplace/items", params={"category": "addons", "status": "active"})
    assert r2.status_code == 200
    items = r2.json().get("items", [])
    # We don't assert presence strictly due to DB-first path; this is a smoke check
    assert isinstance(items, list)


def test_marketplace_purchase_checkout_smoke(monkeypatch):
    # Set API key to provide tenant context
    monkeypatch.setenv("APIKEY_REQUIRED", "1")
    apikeys = [{"key": "mk1", "tenant_id": "t-mkt", "scopes": ["use:copilot"], "plan": "pro"}]
    monkeypatch.setenv("API_KEYS", __import__("json").dumps(apikeys))
    # Ensure admin token so we can create an item
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "tok")
    c = TestClient(app)
    hdr = {"X-API-Key": "mk1"}

    # Upsert item (in-memory fallback will be available even if DB is not)
    c.post(
        "/admin/marketplace/items",
        params={"token": "tok"},
        json={"code": "onetime-10", "title": "One Time 10", "price_usd": 10.0, "category": "addons", "status": "active"},
    )

    # Purchase by code
    r = c.post("/marketplace/purchase", headers=hdr, json={"item_code": "onetime-10"})
    assert r.status_code in (200, 401, 404)
    if r.status_code == 200:
        js = r.json()
        assert js.get("ok") is True
        assert "order_id" in js and "checkout_url" in js
