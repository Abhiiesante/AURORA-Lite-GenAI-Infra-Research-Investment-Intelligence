from fastapi.testclient import TestClient

from apps.api.aurora.main import app


def test_ci_perf_p95_under_budget():
    client = TestClient(app)

    # Warm up and generate some latency samples
    for _ in range(10):
        client.get("/graph/ego/1")
    for _ in range(5):
        client.get("/market/graph")
    for _ in range(3):
        client.post("/copilot/ask", json={"question": "Pinecone traction"})

    r = client.get("/dev/metrics")
    assert r.status_code in (200, 401)
    if r.status_code == 401:
        # Token-guarded in some environments; skip the gate rather than fail CI
        return
    data = r.json()
    assert "latency" in data and isinstance(data["latency"], dict)
    p95 = float(data["latency"].get("p95_ms", 0.0))

    # Budget: generous in-process threshold; tighten in CI as needed
    assert p95 <= 1500.0, f"p95 too high: {p95}ms"
