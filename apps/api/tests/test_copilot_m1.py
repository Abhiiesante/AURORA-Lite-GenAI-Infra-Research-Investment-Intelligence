import json
from fastapi.testclient import TestClient
from aurora.main import app


client = TestClient(app)


def test_copilot_ask_returns_strict_schema_and_citations():
    body = {"session_id": "s1", "question": "Compare Pinecone vs Weaviate traction and risks"}
    res = client.post("/copilot/ask", json=body)
    assert res.status_code == 200, res.text
    data = res.json()
    # schema keys present
    assert set(data.keys()) == {"answer", "comparisons", "top_risks", "sources"}
    assert isinstance(data["comparisons"], list) and len(data["comparisons"]) >= 1
    assert isinstance(data["top_risks"], list) and len(data["top_risks"]) >= 1
    assert isinstance(data["sources"], list) and len(data["sources"]) >= 1
    # citations must be one of retrieved URLs in this scaffolding
    for s in data["sources"]:
        assert s.startswith("https://example.com/")


def test_copilot_rejects_missing_question():
    res = client.post("/copilot/ask", json={"session_id": "s1", "question": "   "})
    assert res.status_code == 400


def test_compare_contract():
    res = client.post("/compare", json={"companies": ["a", "b"], "metrics": ["signal_score", "stars_30d"]})
    assert res.status_code == 200
    data = res.json()
    assert "table" in data and "sources" in data
    assert isinstance(data["table"], list) and len(data["table"]) == 2
