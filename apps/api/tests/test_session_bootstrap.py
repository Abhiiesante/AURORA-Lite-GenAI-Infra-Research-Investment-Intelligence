from contextlib import contextmanager

from fastapi.testclient import TestClient


def test_copilot_ask_session_bootstrap_without_db(monkeypatch):
    # Patch get_session to avoid real DB and track add/commit calls
    import aurora.main as m

    calls = {"add": 0, "commit": 0}

    class FakeSession:
        def add(self, _):
            calls["add"] += 1

        def commit(self):
            calls["commit"] += 1

    @contextmanager
    def fake_get_session():
        yield FakeSession()

    monkeypatch.setattr(m, "get_session", fake_get_session)

    client = TestClient(m.app)
    res = client.post(
        "/copilot/ask",
        json={"session_id": "s-test", "question": "Compare Pinecone vs Weaviate"},
    )

    assert res.status_code == 200, res.text
    data = res.json()
    assert set(data.keys()) == {"answer", "comparisons", "top_risks", "sources"}
    assert isinstance(data["sources"], list) and len(data["sources"]) >= 1
    # Ensure our fake session was used
    assert calls["add"] >= 1 and calls["commit"] >= 1
