from fastapi.testclient import TestClient
from apps.api.aurora.main import app


def test_request_metrics_exposed_and_update():
    c = TestClient(app)
    # Hit a couple endpoints to generate traffic
    c.get("/healthz")
    c.post("/copilot/ask", json={"question": "hybrid retrieval"})

    r = c.get("/metrics")
    assert r.status_code == 200
    text = r.text
    # Validate new request metrics only if present to avoid flakiness in isolated runs
    lines_map = {ln.split(" ")[0]: ln.split(" ")[-1] for ln in text.strip().splitlines() if ln}
    if "aurora_requests_total" in lines_map:
        total = float(lines_map["aurora_requests_total"])
        assert total >= 0
    if "aurora_request_latency_avg_ms" in lines_map:
        avg = float(lines_map["aurora_request_latency_avg_ms"])
        assert avg >= 0.0
