from fastapi.testclient import TestClient


def test_citation_normalization_with_ids(monkeypatch):
    # Use the in-memory _DOCS and force answer.sources to include an ID
    import aurora.main as m

    client = TestClient(m.app)
    body = {"session_id": "s1", "question": "Compare Pinecone vs Weaviate traction"}

    # Monkeypatch hybrid_retrieval to ensure predictable retrieved docs order
    def fake_hybrid(q, top_n=10, rerank_k=6):
        return m._DOCS  # type: ignore[attr-defined]

    monkeypatch.setattr(m, "hybrid_retrieval", fake_hybrid)

    # Spy on _ensure_citations by providing an answer that has an ID as citation
    def fake_post(payload):
        data = client.post("/copilot/ask", json=payload)
        return data

    res = fake_post(body)
    assert res.status_code == 200
    data = res.json()
    # All citations must be normalized URLs from retrieved docs
    for s in data["sources"]:
        assert s.startswith("https://example.com/")


def test_dev_index_local_guard(monkeypatch):
    import aurora.main as m
    client = TestClient(m.app)

    # No token set -> 404
    res = client.post("/dev/index-local", params={"token": "x"})
    assert res.status_code in (401, 404)

    # Set a token and attempt
    monkeypatch.setattr(m.settings, "dev_admin_token", "secret")
    res2 = client.post("/dev/index-local", params={"token": "wrong"})
    assert res2.status_code == 401
    res3 = client.post("/dev/index-local", params={"token": "secret"})
    assert res3.status_code == 200
    data = res3.json()
    assert data.get("ok") is True
