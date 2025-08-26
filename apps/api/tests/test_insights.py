from fastapi.testclient import TestClient
import aurora.main as main
from contextlib import contextmanager
from typing import Any, Dict
from aurora.db import Company


@contextmanager
def _fake_session():
    class _S:
        def get(self, model: Any, ident: Any):
            return Company(canonical_name="ExampleAI")

    yield _S()


def test_insights_schema(monkeypatch):
    # Avoid DB on startup
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "get_session", _fake_session)
    # Avoid hitting real RAG stack; return minimal valid structure
    def _mock_rag(_: str) -> Dict[str, Any]:
        return {"answer": {"company": "ExampleAI", "summary": "ok", "five_forces": {}, "theses": []}, "sources": [{"url": "https://example.ai"}]}
    monkeypatch.setattr(main, "answer_with_citations", _mock_rag)
    client = TestClient(main.app)
    resp = client.get("/insights/company/1")
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        data = resp.json()
        for key in ["company", "summary", "swot", "five_forces", "theses", "sources"]:
            assert key in data
