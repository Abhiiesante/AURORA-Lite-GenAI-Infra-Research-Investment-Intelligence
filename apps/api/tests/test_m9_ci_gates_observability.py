from fastapi.testclient import TestClient

from apps.api.aurora.main import app


client = TestClient(app)


def test_perf_gate_contract():
    r = client.get("/dev/gates/perf")
    assert r.status_code == 200
    data = r.json()
    for k in ("ok", "p95_ms", "budget_ms", "pass"):
        assert k in data


def test_forecast_gate_contract():
    r = client.get("/dev/gates/forecast", params={"company_id": 1, "metric": "mentions"})
    assert r.status_code == 200
    data = r.json()
    for k in ("company", "metric", "smape", "threshold", "pass"):
        assert k in data


def test_rag_gate_pass_allowed_domain():
    body = {"question": "Pinecone traction", "allowed_domains": ["example.com"], "min_sources": 1}
    r = client.post("/dev/gates/rag", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["pass"] is True
    srcs = data.get("sources") or []
    assert isinstance(srcs, list) and len(srcs) >= 1
    # all sources must be from allowed domains
    from urllib.parse import urlparse
    assert all(urlparse(u).netloc.endswith("example.com") for u in srcs)


def test_rag_strict_gate_contract():
    body = {"question": "Pinecone traction", "allowed_domains": ["example.com"], "min_valid": 1}
    r = client.post("/dev/gates/rag-strict", json=body)
    assert r.status_code == 200
    data = r.json()
    # contract keys
    for k in ("question", "sources", "valid_urls", "min_valid", "allowed", "pass"):
        assert k in data


def test_deals_sourcing_shape_contract():
    r = client.get("/deals/sourcing")
    assert r.status_code == 200
    data = r.json()
    deals = data.get("deals") or []
    assert isinstance(deals, list)
    if deals:
        d0 = deals[0]
        assert "company_id" in d0 and "name" in d0 and "score" in d0
        assert "scoring" in d0 and isinstance(d0["scoring"], dict)
        assert "provenance" in d0 and isinstance(d0["provenance"], dict)


def test_dev_metrics_has_error_fields():
    r = client.get("/dev/metrics")
    assert r.status_code == 200
    data = r.json()
    errs = data.get("errors") or {}
    assert "count" in errs and "rate" in errs


def test_prom_metrics_contains_error_lines():
    r = client.get("/metrics")
    assert r.status_code == 200
    txt = r.text
    assert "aurora_request_errors_total" in txt
    assert "aurora_request_error_rate" in txt


def test_gate_status_contract():
    r = client.get("/dev/gates/status")
    assert r.status_code == 200
    data = r.json()
    # must include four sections and overall pass
    for sec in ("perf", "forecast", "errors", "rag"):
        assert sec in data
        assert isinstance(data[sec], dict)
        assert "pass" in data[sec]
    assert "pass" in data
    assert "thresholds" in data and isinstance(data["thresholds"], dict)


def test_gate_status_strict_mode_contract():
    r = client.get("/dev/gates/status", params={"strict": "true"})
    assert r.status_code == 200
    data = r.json()
    assert "thresholds" in data and data["thresholds"].get("strict") is True
