from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict

import jwt
import pytest
from fastapi.testclient import TestClient

import aurora.main as main
from aurora.db import Company
import aurora.config as cfg


@contextmanager
def _fake_session():
    class _S:
        def get(self, model: Any, ident: Any):
            return Company(canonical_name="ExampleAI")

    yield _S()


def _mock_rag_ok(_: str) -> Dict[str, Any]:
    return {"answer": {"company": "ExampleAI", "summary": "ok", "five_forces": {}, "theses": []}, "sources": [{"url": "https://example.ai"}]}


def test_post_insights_requires_auth_when_secret_set(monkeypatch: pytest.MonkeyPatch):
    # Set secret so auth is enforced
    monkeypatch.setattr(cfg.settings, "supabase_jwt_secret", "secret123")
    # Avoid DB on startup
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "get_session", _fake_session)
    monkeypatch.setattr(main, "answer_with_citations", _mock_rag_ok)
    client = TestClient(main.app)

    # Missing token -> 401
    r = client.post("/insights/company/1")
    assert r.status_code == 401

    # Invalid token -> 401
    r = client.post("/insights/company/1", headers={"Authorization": "Bearer invalid"})
    assert r.status_code == 401

    # Valid token -> 200
    token = jwt.encode({"sub": "user1"}, "secret123", algorithm="HS256")
    r = client.post("/insights/company/1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    # Should include normalized sources array of strings
    assert data.get("sources") == ["https://example.ai"]
