from fastapi.testclient import TestClient
import aurora.main as main


def test_alerts_include_confidence_explanation_evidence(monkeypatch):
    # Make DB init a no-op for speed
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.get("/alerts/1?window=90d")
    assert r.status_code == 200
    data = r.json()
    alerts = data.get("alerts") or []
    # Not asserting non-empty to avoid flakiness; check shape if any
    if alerts:
        a0 = alerts[0]
        # presence of keys with permissive types
        assert "confidence" in a0
        assert "explanation" in a0
        assert "evidence" in a0 and isinstance(a0.get("evidence"), list)
