from fastapi.testclient import TestClient
import aurora.main as main

def test_tool_endpoints_exist(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    assert c.get("/tools/company_lookup", params={"name_or_id": "1"}).status_code == 200
    assert c.post("/tools/compare_companies", json={"companies": [1,2], "metrics": ["signal_score"]}).status_code == 200
    assert c.get("/tools/retrieve_docs", params={"query": "vector"}).status_code == 200
    assert c.get("/tools/trend_snapshot", params={"segment": "infra", "window": "90d"}).status_code == 200


def test_report_builder_stub(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.post("/reports/build", json={"kind": "company", "target_id": 1, "window": "90d"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("kind") == "company" and data.get("pages") == 1
