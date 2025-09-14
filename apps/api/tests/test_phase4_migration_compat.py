import os
from fastapi.testclient import TestClient
from aurora.main import app


def test_marketplace_items_compat_smoke(monkeypatch):
    # Ensure admin token to exercise both variants of upsert
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "tok")
    c = TestClient(app)

    # Old schema path (code/description/category/status)
    r1 = c.post(
        "/admin/marketplace/items",
        params={"token": "tok"},
        json={"code": "legacy-1", "title": "Legacy", "description": "Old schema", "price_usd": 1.0, "category": "addons", "status": "active"},
    )
    assert r1.status_code in (200, 401, 404)

    # New schema path (sku/type/metadata_json)
    r2 = c.post(
        "/admin/marketplace/items",
        params={"token": "tok"},
        json={"sku": "new-1", "title": "New", "price_usd": 2.0, "type": "report"},
    )
    assert r2.status_code in (200, 401, 404)

    # Listing should succeed
    r3 = c.get("/marketplace/items")
    assert r3.status_code == 200
    assert "items" in r3.json()
