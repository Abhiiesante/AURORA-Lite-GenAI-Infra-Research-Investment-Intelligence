from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_playbook_markdown_export():
    c = TestClient(app)
    r = c.get("/playbook/investor/a16z/export", params={"company": "Pinecone", "fmt": "md"})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/markdown")
    body = r.text
    assert "Investor Playbook" in body and "Recommended Pitch" in body
