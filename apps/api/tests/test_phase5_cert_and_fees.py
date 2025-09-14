from fastapi.testclient import TestClient

from apps.api.aurora.main import app


client = TestClient(app)


def test_certification_status_default_none():
    r = client.get("/certifications/status", params={"email": "nobody@example.com"})
    assert r.status_code == 200
    data = r.json()
    assert data["analyst_email"] == "nobody@example.com"
    assert data["status"] in ("none", None)


def test_admin_success_fee_summary_requires_token():
    # Without the admin token, endpoint should not expose data (likely 404)
    r = client.get("/admin/success-fee/summary")
    assert r.status_code in (401, 403, 404)
