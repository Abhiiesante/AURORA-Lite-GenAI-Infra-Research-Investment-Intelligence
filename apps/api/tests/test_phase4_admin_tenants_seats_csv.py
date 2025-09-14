import os
import pytest
from aurora.main import app

from fastapi.testclient import TestClient

# optional smoke: admin CSV for tenants and seats

@pytest.mark.parametrize("path", [
    "/admin/tenants",
    "/admin/seats",
])
def test_admin_tenants_seats_csv_optional(path):
    client = TestClient(app)
    token = os.environ.get("DEV_ADMIN_TOKEN", "")
    # JSON default should work (200/401/404 tolerated)
    r = client.get(f"{path}?token={token}")
    assert r.status_code in (200, 401, 404)
    if r.status_code == 200:
        assert r.headers.get("content-type", "").lower().startswith("application/json")
        # CSV variant
        r2 = client.get(f"{path}?token={token}&format=csv")
        assert r2.status_code in (200, 401, 404)
        if r2.status_code == 200:
            ctype = r2.headers.get("content-type", "").lower()
            # Accept text/csv if implemented, or JSON if server ignores the flag
            assert ("text/csv" in ctype) or ("application/json" in ctype)
            body = r2.text.strip()
            assert "," in body or "\n" in body
