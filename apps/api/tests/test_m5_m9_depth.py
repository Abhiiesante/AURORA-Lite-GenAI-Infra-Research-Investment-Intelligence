from fastapi.testclient import TestClient
import aurora.main as main


def test_graph_similar_endpoint_exists_and_safe(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.get("/graph/similar/1", params={"limit": 3})
    assert r.status_code == 200
    data = r.json()
    assert data.get("company") == "1"
    assert "similar" in data


def test_ingest_schedule_and_status(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.post("/ingest/schedule", json={"job": "refresh-topics"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("scheduled") is True and data.get("job") == "refresh-topics"
    r2 = c.get("/ingest/status")
    assert r2.status_code == 200
    assert isinstance(r2.json().get("schedules"), list)


def test_jobs_health_contains_evals_and_schedules(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    # ensure at least one schedule exists
    c.post("/ingest/schedule", json={"job": "refresh-companies"})
    r = c.get("/jobs/health")
    assert r.status_code == 200
    data = r.json()
    assert "evals" in data and isinstance(data["evals"], dict)
    assert "schedules" in data and isinstance(data["schedules"], list)


def test_metrics_expanded_with_hit_ratio_and_evals(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.get("/metrics")
    assert r.status_code == 200
    txt = r.text
    assert "aurora_hybrid_cache_hit_ratio" in txt
    assert "aurora_schedules_total" in txt
    assert "aurora_evals_faithfulness" in txt


def test_graph_investors_and_talent_endpoints(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    assert c.get("/graph/investors/1").status_code == 200
    assert c.get("/graph/talent/1").status_code == 200


def test_feeds_endpoints_and_health_count(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.post("/feeds/add", json={"url": "https://blog.example.com/rss"})
    assert r.status_code == 200
    r2 = c.get("/feeds/list")
    assert r2.status_code == 200 and "feeds" in r2.json()
    r3 = c.get("/jobs/health")
    assert r3.status_code == 200 and isinstance(r3.json().get("feeds_count"), int)


def test_ingest_cancel_updates_status(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    # schedule a job
    r = c.post("/ingest/schedule", json={"job": "refresh-topics"})
    assert r.status_code == 200
    data = r.json()
    sched_id = data.get("id")
    assert data.get("scheduled") is True
    assert sched_id is not None
    # cancel it
    rc = c.post(f"/ingest/cancel/{sched_id}")
    assert rc.status_code == 200 and rc.json().get("ok") is True
    # verify status reflects cancellation
    rs = c.get("/ingest/status")
    assert rs.status_code == 200
    items = rs.json().get("schedules") or []
    # find by id
    found = None
    for it in items:
        if it.get("id") == sched_id:
            found = it
            break
    assert found is not None and found.get("status") == "canceled"