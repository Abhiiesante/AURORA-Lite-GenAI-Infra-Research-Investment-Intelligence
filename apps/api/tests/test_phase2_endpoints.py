from fastapi.testclient import TestClient
import aurora.main as main
import aurora.copilot as copilot


def test_copilot_ask_contract(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    # Avoid hitting DB and external retrieval
    monkeypatch.setattr(copilot, "tool_company_lookup", lambda *_args, **_kw: {})
    monkeypatch.setattr(copilot, "answer_with_citations", lambda _q: {"sources": [{"url": "https://example.ai"}]})
    client = TestClient(main.app)
    r = client.post("/copilot/ask", json={"question": "Compare A vs B"})
    assert r.status_code == 200
    data = r.json()
    assert set(["answer", "comparisons", "top_risks", "sources"]) <= set(data.keys())


def test_compare_contract(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    client = TestClient(main.app)
    r = client.post("/compare", json={"companies": [1, 2], "metrics": ["signal_score", "stars_30d"]})
    assert r.status_code == 200
    data = r.json()
    assert "comparisons" in data and isinstance(data["comparisons"], list)


def test_dashboards_and_trends_contract(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    client = TestClient(main.app)
    assert client.get("/company/1/dashboard").status_code == 200
    assert client.get("/trends/top").status_code == 200
    assert client.get("/trends/1").status_code == 200
    assert client.get("/graph/ego/1").status_code == 200
