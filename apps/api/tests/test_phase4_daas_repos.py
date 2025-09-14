import os
import importlib
from typing import Optional
from fastapi.testclient import TestClient


def get_app_with_env(token: Optional[str] = None):
    if token:
        os.environ["DEV_ADMIN_TOKEN"] = token
    from apps.api.aurora import main as aurora_main
    importlib.reload(aurora_main)
    return aurora_main.app


def test_daas_export_repos_ndjson_shape():
    app = get_app_with_env()
    client = TestClient(app)
    r = client.get("/daas/export/repos")
    assert r.status_code == 200
    body = r.text.strip()
    if not body:
        # empty is allowed
        return
    # Ensure NDJSON format (one JSON object per line)
    for line in body.splitlines():
        assert line.strip().startswith("{") and line.strip().endswith("}")
