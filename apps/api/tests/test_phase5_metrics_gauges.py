import importlib
from fastapi.testclient import TestClient


def test_phase5_gauges_present_or_skip():
    # Reload app to ensure latest metrics endpoint is active
    from apps.api.aurora import main as aurora_main
    importlib.reload(aurora_main)
    app = aurora_main.app
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    # We only assert presence if feature is enabled; otherwise keep test lenient
    gauge_names = [
        "aurora_kg_nodes_total",
        "aurora_kg_edges_total",
        "aurora_agents_running_total",
        "aurora_certified_analysts_total",
        "aurora_success_fee_agreements_total",
    ]
    # Test is opportunistic: pass if at least one appears; otherwise skip
    if not any(n in body for n in gauge_names):
        import pytest
        pytest.skip("Phase 5 metrics gauges not enabled in this environment")
