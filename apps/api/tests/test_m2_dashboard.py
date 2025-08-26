from fastapi.testclient import TestClient
import aurora.main as main

def test_dashboard_contract():
    client = TestClient(main.app)
    r = client.get("/company/1/dashboard?window=90d")
    assert r.status_code == 200
    data = r.json()
    assert data.get("company") == "1"
    assert isinstance(data.get("kpis"), dict)
    assert "signal_score" in data["kpis"]
    assert isinstance(data.get("sparklines"), list)
    assert "sources" in data


def test_trends_contract():
    client = TestClient(main.app)
    r = client.get("/trends/top?window=90d&limit=1")
    assert r.status_code == 200
    data = r.json()
    assert "topics" in data and isinstance(data["topics"], list)
    assert data.get("window") == "90d"

    r = client.get("/trends/1?window=90d")
    assert r.status_code == 200
    detail = r.json()
    assert detail.get("topic_id") == "1" or detail.get("topic_id") == 1
    assert isinstance(detail.get("series"), list)
    assert detail.get("window") == "90d"
