from fastapi.testclient import TestClient

from apps.api.aurora import main as aurora_main
from apps.api.aurora.main import app
import apps.api.aurora.retrieval as retrieval


def test_rag_strict_fallback_when_sources_empty(monkeypatch):
    # Make copilot_ask return no sources to trigger rag-strict fallback
    def _fake_copilot_ask(*_args, **_kwargs):
        return {"answer": "", "sources": []}

    monkeypatch.setattr(aurora_main, "copilot_ask", _fake_copilot_ask)

    # Make validator report no valid URLs so promotion logic is exercised
    monkeypatch.setattr(
        retrieval,
        "validate_citations",
        lambda _s, _d: {"valid_urls": [], "suggested_urls": []},
        raising=True,
    )
    # Ensure retrieval returns at least one example.com doc so fallback can seed sources
    monkeypatch.setattr(
        aurora_main,
        "hybrid_retrieval",
        lambda *_args, **_kwargs: [{"url": "https://example.com/fallback-doc"}],
        raising=True,
    )

    client = TestClient(app)
    body = {"question": "Pinecone traction", "allowed_domains": ["example.com"], "min_valid": 1}
    r = client.post("/dev/gates/rag-strict", json=body)
    assert r.status_code == 200
    data = r.json()
    # Must pass due to fallback seeding/promotion from retrieved docs
    assert data["pass"] is True, data
    valid = data.get("valid_urls") or []
    assert isinstance(valid, list) and len(valid) >= 1
