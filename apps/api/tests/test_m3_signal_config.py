from fastapi.testclient import TestClient

import aurora.main as main


def test_signal_config_get_put_roundtrip(monkeypatch):
    client = TestClient(main.app)

    # Get defaults
    r = client.get("/signals/config")
    assert r.status_code == 200
    cfg = r.json()
    assert "weights" in cfg and "delta_threshold" in cfg and "alpha" in cfg

    # Update config via PUT
    new_cfg = {
        "weights": {
            "mentions_7d": 0.4,
            "commit_velocity_30d": 0.2,
            "stars_growth_30d": 0.15,
            "filings_90d": 0.15,
            "sentiment_30d": 0.10,
        },
        "delta_threshold": 2.5,
        "alpha": 0.3,
    }
    r2 = client.put("/signals/config", json=new_cfg)
    assert r2.status_code == 200
    assert r2.json().get("ok") is True

    # Re-fetch and verify persisted values
    r3 = client.get("/signals/config")
    assert r3.status_code == 200
    cfg2 = r3.json()
    assert abs(cfg2.get("delta_threshold", 0) - 2.5) < 1e-6
    assert abs(cfg2.get("alpha", 0) - 0.3) < 1e-6
    assert abs(cfg2["weights"]["mentions_7d"] - 0.4) < 1e-6