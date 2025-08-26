from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

import aurora.main as main
from aurora.db import Company


@contextmanager
def _fake_session():
    class _S:
        def get(self, model: Any, ident: Any):
            # Return a minimal Company with a canonical name
            return Company(canonical_name="ExampleAI")

    yield _S()


def _set_fake_env(monkeypatch: pytest.MonkeyPatch):
    # Avoid real DB by patching the get_session context manager
    monkeypatch.setattr(main, "get_session", _fake_session)
    # Avoid touching real DB on startup
    monkeypatch.setattr(main, "init_db", lambda: None)


def test_insights_citation_gate(monkeypatch: pytest.MonkeyPatch):
    _set_fake_env(monkeypatch)

    # Mock RAG to return no citations
    def fake_answer(_: str) -> Dict[str, Any]:
        return {"answer": {"company": "ExampleAI"}, "sources": []}

    monkeypatch.setattr(main, "answer_with_citations", fake_answer)

    client = TestClient(main.app)
    r = client.get("/insights/company/1")
    assert r.status_code == 200
    data = r.json()
    assert data["company"] == "ExampleAI"
    assert isinstance(data.get("sources"), list) and len(data["sources"]) == 0
    # Summary should fall back due to no citations
    assert str(data.get("summary", "")).lower().startswith("insufficient evidence")


def test_insights_strict_schema_enforced(monkeypatch: pytest.MonkeyPatch):
    _set_fake_env(monkeypatch)

    # Mock RAG to return citations but a non-JSON answer body
    def fake_answer(_: str) -> Dict[str, Any]:
        return {
            "answer": "This is not JSON",
            "sources": [{"url": "https://example.ai"}],
        }

    monkeypatch.setattr(main, "answer_with_citations", fake_answer)

    client = TestClient(main.app)
    r = client.get("/insights/company/1")
    assert r.status_code == 200
    data = r.json()
    # Because answer is not valid JSON for schema, endpoint must enforce fallback
    assert str(data.get("summary", "")).strip() == "Insufficient evidence"
    assert data.get("sources") == ["https://example.ai"]
