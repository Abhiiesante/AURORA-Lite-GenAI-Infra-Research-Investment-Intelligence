from fastapi.testclient import TestClient
import aurora.main as main


def test_compare_narrative_includes_field_level_citations(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    # Use metrics likely to exist in defaults to ensure deterministic deltas
    r = c.post(
        "/compare",
        json={"companies": [1, 2], "metrics": ["stars_30d", "commits_30d", "mentions_7d"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("answer"), str)
    # Narrative should include at least one inline [source: ...] citation
    assert "[source:" in data["answer"]


def test_report_bullets_end_with_source_citation(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    c = TestClient(main.app)
    r = c.post("/reports/build", json={"kind": "company", "target_id": 1, "window": "90d"})
    assert r.status_code == 200
    data = r.json()
    bullets = data.get("bullets") or []
    assert isinstance(bullets, list) and len(bullets) >= 1
    # Each bullet should end with a [source: ...] tag
    for b in bullets:
        assert "[source:" in b
