from fastapi.testclient import TestClient
import os

from apps.api.aurora.main import app


client = TestClient(app)


def test_admin_success_fee_summary_positive(monkeypatch):
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "t0")

    # Create agreement
    r = client.post("/admin/success-fee/agreements", headers={}, params={"token": "t0"}, json={
        "tenant_id": 1,
        "percent_fee": 0.05,
        "active": True,
    })
    assert r.status_code == 200
    agreement_id = r.json().get("id")

    # Create intro
    r2 = client.post("/admin/success-fee/intro", params={"token": "t0"}, json={
        "agreement_id": agreement_id,
        "company_uid": "company:1",
    })
    assert r2.status_code == 200
    intro_id = r2.json().get("id")

    # Close intro with a deal value
    r3 = client.post("/admin/success-fee/close", params={"token": "t0"}, json={
        "intro_id": intro_id,
        "deal_value_usd": 1000.0,
    })
    assert r3.status_code == 200
    fee = r3.json().get("computed_fee_usd")
    assert abs(fee - 50.0) < 1e-6

    # Summary should include tenant 1 with total_fee_usd ~ 50
    r4 = client.get("/admin/success-fee/summary", params={"token": "t0", "tenant_id": 1})
    assert r4.status_code == 200
    items = r4.json().get("summary") or []
    assert items and any(it.get("tenant_id") == 1 and abs(float(it.get("total_fee_usd", 0)) - 50.0) < 1e-6 for it in items)


def test_snapshot_sign_and_verify(monkeypatch):
    monkeypatch.setenv("DEV_ADMIN_TOKEN", "adm1")
    monkeypatch.setenv("AURORA_SNAPSHOT_SIGNING_SECRET", "secret123")
    r = client.post("/admin/kg/snapshot", params={"token": "adm1"}, json={"notes": "t"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("snapshot_hash")
    assert data.get("signature")
    r2 = client.post("/kg/snapshot/verify", json={
        "snapshot_hash": data["snapshot_hash"],
        "signature": data["signature"],
    })
    assert r2.status_code == 200
    assert r2.json().get("valid") is True


def test_provenance_bundle_deterministic():
    # Same request twice should produce identical provenance bundle id
    r1 = client.post("/forecast/run", json={"company_id": 1, "horizon_weeks": 4})
    r2 = client.post("/forecast/run", json={"company_id": 1, "horizon_weeks": 4})
    assert r1.status_code == 200 and r2.status_code == 200
    b1 = r1.json().get("provenance", {}).get("bundle_id")
    b2 = r2.json().get("provenance", {}).get("bundle_id")
    assert b1 and b2 and b1 == b2
