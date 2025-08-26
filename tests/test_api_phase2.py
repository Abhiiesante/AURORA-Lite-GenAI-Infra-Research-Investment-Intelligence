from fastapi.testclient import TestClient

from apps.api.aurora.main import app


client = TestClient(app)


def test_copilot_ask_citations_present_and_sanitized():
    resp = client.post("/copilot/ask", json={"question": "qdrant traction"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "sources" in data and isinstance(data["sources"], list)
    assert "citations" in data and isinstance(data["citations"], list)
    # Sources must be https URLs and from our in-memory corpus domain in fallback
    assert all(isinstance(u, str) and u.startswith("https://") for u in data["sources"])  # type: ignore
    assert all(c.get("url", "").startswith("https://") for c in data["citations"])  # type: ignore
    assert all(u.startswith("https://example.com/") for u in data["sources"])  # type: ignore


def test_copilot_ask_session_hides_citations():
    resp = client.post("/copilot/ask", json={"question": "weaviate commits", "session_id": "abc"})
    assert resp.status_code == 200
    data = resp.json()
    assert "citations" not in data
    assert isinstance(data.get("sources"), list)


def test_metrics_endpoint_basic():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    text = resp.text
    assert "aurora_hybrid_cache_hits" in text
    assert "aurora_docs_cache_size" in text


def test_compare_endpoints():
    # POST /compare
    resp = client.post("/compare", json={"companies": ["A", "B"], "metrics": ["m1", "m2"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "comparisons" in body and isinstance(body["comparisons"], list)
    assert "table" in body and isinstance(body["table"], list)
    # GET /compare
    resp2 = client.get("/compare", params=[("companies", "A"), ("companies", "B"), ("metric", "m1")])
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert "rows" in body2 and isinstance(body2["rows"], list)
