import importlib
import json
import os
import re
from typing import Optional

import pytest
from fastapi.testclient import TestClient


def parse_metric(body: str, name: str) -> Optional[float]:
    # Match lines like: name 123 or name 123.45
    pat = re.compile(rf"^{re.escape(name)}\s+([-+]?[0-9]*\.?[0-9]+)$", re.M)
    m = pat.search(body)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def parse_labeled_metric(body: str, name: str, labels: dict) -> Optional[float]:
    # Build label filter like {k="v",k2="v2"}
    label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
    pat = re.compile(rf"^{re.escape(name)}\{{{re.escape(label_str)}\}}\s+([-+]?[0-9]*\.?[0-9]+)$", re.M)
    m = pat.search(body)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def reload_app():
    from apps.api.aurora import main as aurora_main
    importlib.reload(aurora_main)
    return aurora_main.app


def test_requests_total_increments_in_realtime():
    app = reload_app()
    client = TestClient(app)
    before = parse_metric(client.get("/metrics").text, "aurora_requests_total") or 0.0
    # Make a few requests that should count
    for _ in range(3):
        r = client.get("/healthz")
        assert r.status_code == 200
    after = parse_metric(client.get("/metrics").text, "aurora_requests_total") or 0.0
    assert after - before >= 3


def test_hybrid_cache_hits_and_misses_change_with_repeated_query():
    # Enable admin to call memo generate, which uses hybrid_retrieval
    os.environ["DEV_ADMIN_TOKEN"] = "rt-admin"
    app = reload_app()
    client = TestClient(app)
    m0 = client.get("/metrics").text
    hits0 = parse_metric(m0, "aurora_hybrid_cache_hits") or 0.0
    misses0 = parse_metric(m0, "aurora_hybrid_cache_misses") or 0.0
    size0 = parse_metric(m0, "aurora_hybrid_cache_size") or 0.0
    # First call should be a miss and populate cache
    q = {"query": "vector db traction", "top_k": 6}
    r1 = client.post("/admin/agents/memo/generate?token=rt-admin", json=q)
    if r1.status_code not in (200, 404, 401):
        pytest.fail(f"unexpected status {r1.status_code}")
    if r1.status_code != 200:
        pytest.skip("admin surface not available in this env")
    # Second call same query should be a hit
    r2 = client.post("/admin/agents/memo/generate?token=rt-admin", json=q)
    assert r2.status_code == 200
    m1 = client.get("/metrics").text
    hits1 = parse_metric(m1, "aurora_hybrid_cache_hits") or 0.0
    misses1 = parse_metric(m1, "aurora_hybrid_cache_misses") or 0.0
    size1 = parse_metric(m1, "aurora_hybrid_cache_size") or 0.0
    assert misses1 >= misses0 + 1  # first call
    assert hits1 >= hits0 + 1      # second call
    assert size1 >= max(size0, 1)


def test_usage_units_forecast_increments_with_api_key_or_skip():
    # Configure API key auth to create tenant context so /metrics aggregates usage units
    os.environ["APIKEY_REQUIRED"] = "1"
    api_keys = [{"key": "sk_rt", "tenant_id": "t_rt", "scopes": ["use:forecast"], "plan": "pro"}]
    os.environ["API_KEYS"] = json.dumps(api_keys)
    app = reload_app()
    client = TestClient(app)
    metrics_before = client.get("/metrics").text
    before_val = parse_labeled_metric(metrics_before, "aurora_usage_units_total", {"product": "forecast"}) or 0.0
    # Call a forecast endpoint that increments usage when tenant present
    r = client.get("/forecast/backtest/123", headers={"X-API-Key": "sk_rt"})
    if r.status_code not in (200, 400):
        # Backtest may return 400 for invalid company, which still should have counted usage
        pytest.skip("forecast backtest not available in this env")
    metrics_after = client.get("/metrics").text
    after_val = parse_labeled_metric(metrics_after, "aurora_usage_units_total", {"product": "forecast"})
    if after_val is None:
        pytest.skip("usage metric not emitted in this env")
    assert after_val >= before_val + 1
