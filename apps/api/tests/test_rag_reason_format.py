from fastapi.testclient import TestClient

# conftest.py inserts apps/api on sys.path; import using the aurora alias
from aurora.main import app  # type: ignore


def test_rag_gate_reason_insufficient_sources():
    client = TestClient(app)
    body = {"question": "Pinecone traction", "allowed_domains": ["example.com"], "min_sources": 10}
    r = client.post("/dev/gates/rag", json=body)
    assert r.status_code == 200
    data = r.json()
    if not data.get("pass"):
        reason = data.get("reason") or ""
        assert reason.startswith("insufficient_sources:") and "<10" in reason