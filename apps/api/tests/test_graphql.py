from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
import aurora.main as main
import aurora.graphql as gql
from contextlib import contextmanager
from typing import Any
from aurora.db import Company


@contextmanager
def _fake_session():
    class _S:
        def get(self, model: Any, ident: Any):
            return Company(id=1, canonical_name="ExampleAI", website="https://example.ai", segments="vector_db", hq_country="US")

        def exec(self, _):
            return iter([
                Company(id=1, canonical_name="ExampleAI", website="https://example.ai", segments="vector_db", hq_country="US")
            ])

    yield _S()


def test_graphql_companies_query(monkeypatch: pytest.MonkeyPatch):
    # Avoid DB on startup
    monkeypatch.setattr(main, "init_db", lambda: None)
    # Patch the resolver's get_session where it's used (aurora.graphql)
    monkeypatch.setattr(gql, "get_session", _fake_session)
    client = TestClient(main.app)
    q = {"query": "{ companies(limit: 1) { id canonicalName website } }"}
    r = client.post("/graphql", json=q)
    assert r.status_code == 200
    data = r.json()
    assert "data" in data and data["data"] is not None and "companies" in data["data"]
    assert data["data"]["companies"][0]["canonicalName"] == "ExampleAI"
