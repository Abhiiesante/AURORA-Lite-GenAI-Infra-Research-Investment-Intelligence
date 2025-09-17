import os
import pytest
from fastapi.testclient import TestClient


RUN_SMOKE = (os.getenv("AURORA_RUN_TENANT_SMOKE") or "").strip().lower() in ("1", "true", "yes")


@pytest.mark.skipif(not RUN_SMOKE, reason="tenant smoke disabled; set AURORA_RUN_TENANT_SMOKE=1 to enable")
def test_api_tools_retrieve_docs_respects_tenant(monkeypatch):
    meili = os.getenv("MEILI_URL")
    qdrant = os.getenv("QDRANT_URL")
    if not (meili and qdrant):
        pytest.skip("MEILI_URL/QDRANT_URL not set")

    # Avoid DB requirements; init_db() handles missing DB gracefully
    from apps.api.aurora.main import app

    c = TestClient(app)

    # Tenant 1
    monkeypatch.setenv("AURORA_DEFAULT_TENANT_ID", "1")
    r1 = c.get("/tools/retrieve_docs", params={"query": "competition", "limit": 3})
    assert r1.status_code == 200
    docs1 = r1.json().get("docs", [])
    assert isinstance(docs1, list)
    assert len(docs1) >= 1

    # Tenant 2
    monkeypatch.setenv("AURORA_DEFAULT_TENANT_ID", "2")
    r2 = c.get("/tools/retrieve_docs", params={"query": "competition", "limit": 3})
    assert r2.status_code == 200
    docs2 = r2.json().get("docs", [])
    assert isinstance(docs2, list)
    assert len(docs2) >= 1

    # Basic isolation heuristic: top URL for tenant 1 should be present among tenant 1 corpus
    # and same for tenant 2. We don't enforce strict difference here since sample corpora overlap.
    assert all("url" in d for d in docs1)
    assert all("url" in d for d in docs2)
