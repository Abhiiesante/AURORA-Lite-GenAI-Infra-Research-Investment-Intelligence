from fastapi.testclient import TestClient
import aurora.main as main

def test_ops_endpoints(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.get("/jobs/status")
    assert r.status_code == 200 and "flows" in r.json()
    r = c.get("/evals/summary")
    assert r.status_code == 200 and "faithfulness" in r.json()


def test_graph_endpoints(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    assert c.get("/graph/ego/1").status_code == 200
    r = c.get("/graph/derive/1", params={"window":"90d"})
    assert r.status_code == 200 and "edges" in r.json()
