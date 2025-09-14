from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_webhook_register_and_unregister_smoke(monkeypatch):
    # Provide tenant via API key
    monkeypatch.setenv("APIKEY_REQUIRED", "1")
    apikeys = [{"key": "w1", "tenant_id": "t-wb", "scopes": ["use:copilot"], "plan": "pro"}]
    monkeypatch.setenv("API_KEYS", __import__("json").dumps(apikeys))
    c = TestClient(app)
    hdr = {"X-API-Key": "w1"}

    # Register webhook
    r = c.post("/webhooks/register", headers=hdr, json={"url": "https://example.com/hook", "event": "usage.threshold", "secret": "s1"})
    assert r.status_code in (200, 401)
    if r.status_code == 200:
        # Unregister
        u = c.delete("/webhooks/register", headers=hdr, params={"url": "https://example.com/hook", "event": "usage.threshold"})
        assert u.status_code in (200, 401)


def test_daas_filings_export_smoke():
    c = TestClient(app)
    r = c.get("/daas/export/filings")
    # Always returns NDJSON, even if empty
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/x-ndjson")
