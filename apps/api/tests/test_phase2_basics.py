from fastapi.testclient import TestClient
from apps.api.aurora.main import app, settings


client = TestClient(app)


def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ask_requires_citations():
    r = client.post("/copilot/ask", json={"question": "What is the report?"})
    assert r.status_code == 200
    data = r.json()
    assert "citations" in data and len(data["citations"]) > 0
    assert data["citations"][0]["url"].startswith("http")


def test_compare_basic():
    r = client.get("/compare", params={"companies": ["Acme", "Globex"], "metric": "revenue"})
    assert r.status_code == 200
    data = r.json()
    assert "rows" in data and len(data["rows"]) == 2
    assert "audit" in data


def test_dev_index_guard():
    r = client.post("/dev/index-local", params={"token": "x"})
    assert r.status_code in (401, 404)

    # Set token and retry
    from apps.api.aurora.config import settings as cfg

    cfg.dev_admin_token = "secret"
    r2 = client.post("/dev/index-local", params={"token": "wrong"})
    assert r2.status_code == 401
    r3 = client.post("/dev/index-local", params={"token": "secret"})
    assert r3.status_code == 200
    assert r3.json().get("ok") is True
