from fastapi.testclient import TestClient
import aurora.main as main


def test_dev_refresh_topics_guard_and_effect(monkeypatch):
    # Guarded endpoint returns 404 until token configured
    c = TestClient(main.app)
    r = c.post("/dev/refresh-topics", params={"token": "x"})
    assert r.status_code in (401, 404)

    # Set token and try again
    from apps.api.aurora.config import settings as cfg
    cfg.dev_admin_token = "secret"
    r2 = c.post("/dev/refresh-topics", params={"token": "secret"})
    assert r2.status_code == 200
    data = r2.json()
    assert data.get("ok") is True

    # trends/top should still respond and include enriched fields
    r3 = c.get("/trends/top")
    assert r3.status_code == 200
    topics = r3.json().get("topics") or []
    if topics:
        t0 = topics[0]
        assert "label" in t0 and "delta" in t0 and "change_flag" in t0
        # Enriched helpers may or may not be present depending on data, but check keys exist if present
        if "top_docs" in t0:
            assert isinstance(t0["top_docs"], list)
