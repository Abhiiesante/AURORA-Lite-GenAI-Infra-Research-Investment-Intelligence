# Weekly Runbooks

## RAG Eval (ragas-weekly)
- Schedule: Mondays 06:00 UTC
- Inputs: optional RAG_GOLDEN_PATH (file of questions)
- Output: ragas_ci_output.txt artifact and job summary
- Gates: faithfulness>=0.90, relevancy>=0.75, recall>=0.70 and WoW dip checks

## Market Perf (market-weekly)
- Schedule: Mondays 06:15 UTC
- Params: CI_MARKET_PAGE_SIZE, CI_MARKET_RUNS, MARKET_P95_BUDGET_MS
- Output: market_gate_output.txt artifact and job summary
- Promotion: flip CI_MARKET_GATE=1 in main CI after consistent greens

## Gate Status triage
- Endpoint: `GET /dev/gates/status?strict=false`
- If `pass=false`:
	- Inspect `gates.perf.p95` vs `PERF_P95_BUDGET_MS` and `/metrics` latency gauges
	- Check `gates.errors.error_rate` vs `ERROR_RATE_MAX`; enable SLO webhook envs for alerts
	- Review `gates.forecast.smape` and adjust `SMAPE_MAX` or per-metric overrides
	- For RAG failures: verify `ALLOWED_RAG_DOMAINS` and source normalization in `/copilot/ask`

### How to interpret Gate Status
- perf: p95 must be below budget; if close to the threshold, watch trends and consider tightening cache TTLs.
- errors: sustained error rate indicates an incident; correlate with logs/traces; burn alerts help with paging.
- forecast: SMAPE drift suggests data distribution shifts; retrain or adjust per-metric thresholds.
- rag: failing strict checks points to retrieval indexing or allowlist issues.

## SLO burn alerts
- Configure `SLO_WEBHOOK_URL` and `SLO_ERROR_RATE_BURN`
- `/dev/metrics` will POST `{ kind: "slo_burn", error_rate, window }` when breached

Example payload:

```json
{
	"kind": "slo_burn",
	"ts": "2025-08-31T10:20:30Z",
	"error_rate": 0.067,
	"window_size": 50,
	"service": "aurora-lite-api"
}
```
