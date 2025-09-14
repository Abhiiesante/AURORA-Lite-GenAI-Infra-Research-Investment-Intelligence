# CI Gates

This repo exposes lightweight HTTP gates and a Python script to enforce investor-grade quality in CI.

## Endpoints

- GET /dev/gates/perf
  - Compares current p95 (ms) to budget from `PERF_P95_BUDGET_MS` (default 1500).
  - Uses sliding window size `METRICS_WINDOW_SAMPLES` (default 50).

- GET /dev/gates/forecast
  - Runs backtest and ensures SMAPE <= threshold from `SMAPE_MAX` or `SMAE_MAX` (default 80).
  - Supports per-metric overrides: `SMAPE_MAX_<METRIC>` (e.g., `SMAPE_MAX_mentions=65`).

- GET /dev/gates/errors
  - Ensures error rate <= `ERROR_RATE_MAX` (default 0.02).

- POST /dev/gates/rag
  - Body: `{ "question": str, "allowed_domains": ["example.com"], "min_sources": 1 }`
  - Validates retrieved sources belong to allowed_domains and satisfy min_sources.

- POST /dev/gates/rag-strict
  - Body: `{ "question": str, "allowed_domains": ["example.com"], "min_valid": 1 }`
  - Calls `/copilot/ask` and validates its returned sources using the citation validator and allowed domains.

- GET /dev/gates/market-perf
  - Exercises Market Map API and checks p95 against `MARKET_P95_BUDGET_MS` (default 2000).

## Script

- `python scripts/ci_gates.py` runs all gates using FastAPI TestClient.
  - Env vars:
    - PERF_P95_BUDGET_MS (ms)
    - METRICS_WINDOW_SAMPLES
    - SMAPE_MAX or SMAE_MAX (percent)
    - ERROR_RATE_MAX (ratio)
    - ALLOWED_RAG_DOMAINS (comma-separated list)
    - RAG_MIN_SOURCES

## Workflow

`.github/workflows/ci.yml` runs pytest and then the CI gates script.

Adjust thresholds via repo/environment secrets without changing code.

## Triage tips

- perf gate: Inspect `/metrics` p95/p99; look for hot endpoints; enable OTel and check spans with high durations; consider increasing cache TTLs.
- errors gate: Check logs around the failure time and recent deployments; see `/dev/metrics` for window stats; configure SLO webhook for alerting.
- forecast gate: Compare backtest SMAPE across models (`?model=ema|lr`); adjust per-metric thresholds if one metric dominates.
- rag gates: Verify allowlist (`ALLOWED_RAG_DOMAINS`) and document normalization; re-index if retrieval is stale.

## CI Toggles

- `CI_MARKET_GATE=1` promotes the Market Perf gate into the main CI gate set (off by default). Weekly workflows for Market Perf and RAG evals always run.

## Status Aggregator

- `GET /dev/gates/status?strict=false` returns:
  - `gates`: perf/errors/forecast/rag/market with thresholds
  - `evals`: latest RAG and market eval summaries
  - `pass`: overall decision (strict toggles stricter RAG checks)

Example response (truncated):

```json
{
  "pass": true,
  "gates": {
    "perf": { "p95_ms": 810, "budget_ms": 1500, "pass": true },
    "errors": { "error_rate": 0.01, "max": 0.02, "pass": true },
    "forecast": { "metric": "mentions", "smape": 62.4, "threshold": 65, "pass": true },
    "rag": { "min_sources": 2, "valid": 3, "allowed_domains": ["example.com"], "pass": true },
    "market": { "p95_ms": 1650, "budget_ms": 2000, "runs": 5, "size": 400, "pass": true }
  },
  "evals": {
    "rag": { "faithfulness": 0.92, "relevancy": 0.78, "recall": 0.73, "pass": true },
    "market": { "p95_ms": 1800, "pass": true }
  },
  "thresholds": {
    "perf_p95_ms": 1500,
    "market_p95_ms": 2000,
    "error_rate_max": 0.02,
    "smape_max_default": 80
  }
}
```

## SLO Webhook (optional)

- Set `SLO_WEBHOOK_URL` and `SLO_ERROR_RATE_BURN` to receive JSON alerts from `/dev/metrics` when error rates exceed threshold.
