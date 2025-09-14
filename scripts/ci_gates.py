import os
import sys
from typing import List, Dict, Any

from fastapi.testclient import TestClient

try:
    from apps.api.aurora.main import app
except Exception as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)


def _fail(msg: str) -> None:
    print(msg)
    sys.exit(1)


def main() -> None:
    client = TestClient(app)

    # Hit a couple endpoints to warm up metrics
    client.get("/healthz")
    client.get("/dev/metrics")

    # Perf gate
    r = client.get("/dev/gates/perf")
    if r.status_code != 200:
        _fail(f"perf gate HTTP {r.status_code}")
    perf = r.json()
    if not perf.get("pass", False):
        _fail(f"perf gate failed: p95={perf.get('p95_ms')} budget={perf.get('budget_ms')}")

    # Forecast gate
    company_id = int(os.environ.get("CI_FORECAST_COMPANY_ID", "1"))
    metric = os.environ.get("CI_FORECAST_METRIC", "mentions")
    r = client.get("/dev/gates/forecast", params={"company_id": company_id, "metric": metric})
    if r.status_code != 200:
        _fail(f"forecast gate HTTP {r.status_code}")
    fc = r.json()
    if not fc.get("pass", False):
        _fail(f"forecast gate failed: smape={fc.get('smape')} thr={fc.get('threshold')}")

    # RAG gate
    allowed: List[str] = [s.strip() for s in os.environ.get("ALLOWED_RAG_DOMAINS", "example.com").split(",") if s.strip()]
    min_sources = int(os.environ.get("RAG_MIN_SOURCES", "1"))
    r = client.post("/dev/gates/rag", json={"question": "Pinecone traction", "allowed_domains": allowed, "min_sources": min_sources})
    if r.status_code != 200:
        _fail(f"rag gate HTTP {r.status_code}")
    rag = r.json()
    if not rag.get("pass", False):
        _fail(f"rag gate failed: reason={rag.get('reason')} sources={rag.get('sources')}")

    # Strict RAG gate (supports golden tests)
    golden_path = os.environ.get("RAG_STRICT_GOLDEN", os.path.join(os.getcwd(), "tests", "goldens", "rag_strict.json"))
    golden_cases: List[Dict[str, Any]] = []
    try:
        if os.path.exists(golden_path):
            import json as _json
            with open(golden_path, "r", encoding="utf-8") as f:
                golden_cases = _json.load(f)
    except Exception:
        golden_cases = []
    if not golden_cases:
        golden_cases = [{"question": "Pinecone traction", "allowed_domains": allowed, "min_valid": min_sources}]
    for case in golden_cases:
        payload = {
            "question": case.get("question") or "Pinecone traction",
            "allowed_domains": case.get("allowed_domains") or allowed,
            "min_valid": int(case.get("min_valid") or min_sources),
        }
        r = client.post("/dev/gates/rag-strict", json=payload)
        if r.status_code != 200:
            _fail(f"rag-strict gate HTTP {r.status_code} for question='{payload['question']}'")
        rags = r.json()
        if not rags.get("pass", False):
            _fail(f"rag-strict gate failed for question='{payload['question']}': valid_urls={rags.get('valid_urls')} allowed={payload['allowed_domains']}")

    # Error-rate gate
    r = client.get("/dev/gates/errors")
    if r.status_code != 200:
        _fail(f"errors gate HTTP {r.status_code}")
    eg = r.json()
    if not eg.get("pass", False):
        _fail(f"errors gate failed: rate={eg.get('rate')} thr={eg.get('threshold')}")

    # Optional: Market perf gate (non-gating by default). Enable with CI_MARKET_GATE=1
    if os.environ.get("CI_MARKET_GATE", "0") == "1":
        params = {
            "size": int(os.environ.get("CI_MARKET_PAGE_SIZE", "400")),
            "runs": int(os.environ.get("CI_MARKET_RUNS", "7")),
        }
        r = client.get("/dev/gates/market-perf", params=params)
        if r.status_code != 200:
            _fail(f"market-perf gate HTTP {r.status_code}")
        mg = r.json()
        if not mg.get("pass", False):
            _fail(f"market-perf gate failed: p95={mg.get('p95_ms')} budget={mg.get('budget_ms')} size={mg.get('size')}")

    print("CI gates passed")


if __name__ == "__main__":
    main()
