from fastapi.testclient import TestClient
import aurora.main as main

def test_signal_series_contract(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.get("/signal/1?window=90d")
    assert r.status_code == 200
    data = r.json()
    assert data.get("company") == "1"
    assert isinstance(data.get("series"), list)
    if data["series"]:
        assert "date" in data["series"][0] and "signal_score" in data["series"][0]
