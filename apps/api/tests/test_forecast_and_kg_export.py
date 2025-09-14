from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.aurora.main import app


client = TestClient(app)


def test_forecast_run_enrichment():
    resp = client.post("/forecast/run", json={"company_id": 1, "horizon_weeks": 4})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("median"), list)
    assert isinstance(data.get("alerts"), list)
    assert isinstance(data.get("sources"), list)
    prov = data.get("provenance")
    assert isinstance(prov, dict)
    assert "bundle_id" in prov


def test_kg_export_forecast_deterministic():
    r1 = client.get("/kg/export/forecast/1")
    r2 = client.get("/kg/export/forecast/1")
    assert r1.status_code == 200 and r2.status_code == 200
    d1, d2 = r1.json(), r2.json()
    assert "nodes" in d1 and "edges" in d1 and "snapshot_hash" in d1
    assert isinstance(d1["nodes"], list) and isinstance(d1["edges"], list)
    assert d1["snapshot_hash"] == d2["snapshot_hash"]
