# AURORA-Lite — GenAI Infra Research & Investment Intelligence (Student Zero-Cost Stack)

A zero-cost, local-first platform for real-time research on Generative AI infrastructure companies. Ingests open sources, builds a small knowledge graph and vector index, and serves investor-grade briefs with citations using local models.
Next.js app in `apps/web`. Set `NEXT_PUBLIC_API_URL` to point to the API.

New pages (Phase 3):
- /market-map – interactive market map with segment filter and JSON export
- /alerts – grouped alerts with evidence tooltips
- /deals – deal candidates, generate auto-memo, export PDF
- /forecast – time-series forecast + what-if shock
- /people – people graph
- /investors – investor profile + syndication graph

Demo walkthrough (≈8 minutes):
1) Market overview: open /market-map, filter by segment and min signal; export the JSON.
2) Alerts triage: open /alerts, hover tooltips, click evidence.
3) Deal room: open /deals, select a candidate, Generate Memo, Export PDF.

Artifacts produced:
- market_export.json (from /market-map)
- memo.pdf (from /deals)
- Optional: screenshot of /alerts filtered list
## Phase 0 MVP (North-Star)

## Quick start (local)
Prefect flows exist in `pipelines/ingest` and wrappers in `flows/`.
- Ingest: `flows/ingest_rss.py`, `flows/ingest_github.py`, `flows/ingest_edgar.py` (uses `pipelines/ingest/*_flow.py`)
- Upserts: `flows/upsert_postgres.py` into SQLModel tables (NewsItem, Filing, Repo)
- Weekly compute: `flows/compute_weekly.py` persists `SignalSnapshot` and `Alert`
- Orchestration entrypoint: `flows/schedule_weekly.py` to ingest then compute
2. Copy `.env.example` to `.env` and fill minimal secrets.
3. docker compose up -d
4. Open UI at http://localhost:3000 and API at http://localhost:8000/docs

## AURORA-Lite Phase 2 (Acceptance Overview)

This repo implements Phase 2 milestones M1–M10. Highlights: strict JSON contracts, enforced citations, hybrid retrieval, topic trends, market graph, local-first persistence, observability, eval gates, ETag caching, and ISR.
$env:PYTHONUTF8=1; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -m uvicorn main:app --app-dir apps/api --host 127.0.0.1 --port 8000 --reload
Quickstart:

1) Create and activate a Python 3.11 venv
2) Install deps: `pip install -e .` (or `pip install -r requirements.txt`)
3) Copy `.env.local.example` to `.env` and tweak values if needed
4) Run tests: `pytest`
5) Start API: `uvicorn apps.api.aurora.main:app --reload` (or use VS Code task "API: Run (uvicorn)")
6) Optional: apply DB migrations with Alembic: `alembic upgrade head`
7) Optional: seed demo data for /compare: `python scripts/seed_demo_data.py` (or use VS Code task "DB: seed demo data")

Key endpoints:
- POST /copilot/ask
- POST /compare
- GET /company/{id}/dashboard
- GET /trends/top, GET /trends/{topic_id}
 - GET /graph/ego/{company_id}
 - POST /dev/index-local (guarded by DEV_ADMIN_TOKEN)
 - Tools: /tools/retrieve_docs, /tools/company_lookup, /tools/compare_companies (supports window), /tools/trend_snapshot, /tools/detect_entities

All responses include sources[] and strict schemas.

### Admin/Auth quick notes
- DEV_ADMIN_TOKEN: set in environment or in `apps.api.aurora.config.settings.dev_admin_token`. Pass as `?token=...` or via header `X-Dev-Token: ...` (both accepted uniformly). If unset, admin/dev endpoints return 404.
- API keys: disabled by default. To require keys for insights-only surfaces, set `APIKEY_REQUIRED=1`. Header name defaults to `X-API-Key` (configurable via `apikey_header_name`). Public endpoints like `/healthz`, `/metrics`, and `/dev/metrics` remain accessible.

UI pages (Next.js):
- /market-map — Market graph from API
- /trends — Trend Explorer (topics + series)
- /compare — Side-by-side compare with narrative + citations
- /dashboard — Company dashboard with “Explain this chart” calling insights

Acceptance checklist (Phase 2):
- [x] M1: Research Copilot v2 — strict JSON, citations enforced, hybrid retrieval
- [x] M2: Dashboard + Trends contracts — KPIs, sparklines, topic series
- [x] M3: Signals/Alerts — signal series and alert endpoints
- [x] M4: Topics — BERTopic-gated pipeline, periodic refit, persist Topic/TopicTrend
- [x] M5: Schedules — DB-backed JobSchedule; list/cancel/status
- [x] M6: Field-level citations — compare narrative with inline [source: ...]
- [x] M7: Graph helpers — ego/similar/investors/talent and market map API
- [x] M8: Feeds + quality — URL-hash dedup, optional LSH, language/timestamp checks
- [x] M9: Evals — baseline summary and artifact endpoint; CI guard tests
- [x] M10: UX/perf — ETag caching, ISR proxy route, client ETag-aware fetch

See docs/ACCEPTANCE.md for how to verify each milestone locally.
## Monorepo layout
- apps/api — FastAPI service (REST + RAG endpoints)
See docs/PRD.md for detailed requirements and docs/architecture.md for diagrams.

## License
MIT

---

## Phase 3 additions (quick reference)

- Observability
	- GET /dev/metrics — request_count, avg, p50/p95/p99, errors{count,rate}, cache stats
	- GET /metrics — Prometheus text with cache + request and error metrics
	- GET /dev/perf/ego-check — ego graph perf check (token-guarded)

- CI Gates (investor-grade checks)
	- GET /dev/gates/perf — compares current p95 to PERF_P95_BUDGET_MS
	- GET /dev/gates/forecast — SMAPE vs SMAPE_MAX/SMAE_MAX for backtest
	- GET /dev/gates/errors — error rate vs ERROR_RATE_MAX
	- POST /dev/gates/rag — validates retrieved sources against allowed_domains and min_sources
	- POST /dev/gates/rag-strict — calls /copilot/ask and validates normalized sources against retrieved docs and allowed domains
	- GET /dev/gates/status — aggregate status (perf/forecast/errors/rag); supports `?strict=true` and returns `thresholds` metadata
	- Script: scripts/ci_gates.py (runs all gates)
	- See docs/CI_GATES.md for env knobs

- People/Investor Graph
	- GET /people/graph/{company_id}
	- GET /graph/investors/{company_id}
	- GET /graph/talent/{company_id}

- Investors & Playbook
	- GET /investors/profile/{vc}
	- GET /investors/syndicates/{vc}
	- GET /playbook/investor/{vc}?company=ACME

- Deals & Forecasts
	- GET /deals/sourcing?limit=10
	- GET /forecast/{company_id}?metric=mentions&horizon=6

## Phase 3 — Ops & Toggles

Environment knobs to tune gates and behavior without code changes. Add to `.env` or CI secrets.

- Performance & Errors
	- PERF_P95_BUDGET_MS: p95 budget for general perf gate (default 1500)
	- MARKET_P95_BUDGET_MS: p95 budget for Market Map gate (default 2000)
	- METRICS_WINDOW_SAMPLES: sliding window size used by /dev/metrics (default 50)
	- ERROR_RATE_MAX: error-rate ceiling for gate_errors (default 0.02)

- Forecasting
	- SMAPE_MAX: default SMAPE threshold (percent, default 80)
	- SMAPE_MAX_<METRIC>: per-metric override, e.g. SMAPE_MAX_mentions=65
	- Forecast endpoints also accept `?model=ema|lr` at request-time

- RAG (citations)
	- ALLOWED_RAG_DOMAINS: comma-separated allowlist for rag gates
	- RAG_MIN_SOURCES: minimum number of sources required

- CI behavior
	- CI_MARKET_GATE=0|1: promote Market Perf gate into main CI (default 0; weekly workflow always runs)

- Tracing (optional OpenTelemetry)
	- OTEL_EXPORTER_OTLP_ENDPOINT: e.g. http://localhost:4318
	- OTEL_EXPORTER_OTLP_HEADERS: e.g. Authorization=...;api-key=...
	- OTEL_SERVICE_NAME: logical service name for traces (default aurora-lite-api)

- SLO Alerts (optional)
	- SLO_WEBHOOK_URL: if set, /dev/metrics will POST a JSON alert on burn
	- SLO_ERROR_RATE_BURN: error-rate threshold to trigger alert (default 0.05)

Notes
- /dev/gates/status aggregates perf, forecast, errors, rag, market, and includes evals.pass
- Weekly workflows enforce RAG evals and Market Perf; turn on CI_MARKET_GATE after a few green weekly runs
- For slow queries, consider adding simple spans around DB calls and increase cache TTLs for market queries (`_cache_set` in API). See docs/RUNBOOKS.md.
See also docs/OBSERVABILITY.md for example outputs and how to read them.

RBAC & Audit
- Endpoints under /dev/* may be guarded by `DEV_ADMIN_TOKEN`; provide `?token=...` or header `X-Dev-Token: ...`.
- Audit hashing: InsightCache uses a SHA-1 key of `{name, params}`; extend if policy requires stronger hashing.

Cache TTL Tunables
- Retrieval hybrid cache TTL is 600s; docs cache uses `_cache_set(data, ttl_sec=...)` (default 86400s). Documented here for operators.

### Gate Status quick runbook
- Call `GET /dev/gates/status?strict=false` to retrieve:
	- `gates`: perf/errors/forecast/rag/market results with budgets/thresholds
	- `evals`: latest RAG/market eval summaries
	- `pass`: overall boolean (strict adds RAG strict checks and market perf)
- If `perf.pass` is false: correlate with `/metrics` p95; adjust PERF_P95_BUDGET_MS or investigate hot endpoints (enable OTel to see spans).
- If `forecast.pass` is false: tune `SPLIT` and `SMAPE_MAX` or per-metric `SMAPE_MAX_<metric>`; inspect `/forecast/backtest/{id}?metric=...`.
- If `errors.pass` is false: examine recent 5xx logs, reduce METRICS_WINDOW_SAMPLES sensitivity, and set SLO webhook envs to be alerted.

### Durable webhooks (optional)
- Set `DURABLE_WEBHOOKS=1` to enable a background dispatcher with queued deliveries and backoff retry.
- Inspect queue: `GET /admin/webhooks/queue?token=DEV_ADMIN_TOKEN`.
- Metric: `aurora_webhook_queue_depth` in `/metrics`.
- If SQLModel/DB is available, webhook deliveries are queued in table `webhook_queue` for durability; otherwise an in-memory queue is used.

## Phase 4 additions (quick reference)

Monetization & quotas
- Public catalog: `GET /plans`
- Tenant limits: `GET /limits` (requires API key context)
- Usage summary: `GET /usage` and admin export: `GET /admin/usage?format=json|csv&token=...`
- Enable API key enforcement: set `APIKEY_REQUIRED=1`; provide keys via DB (api_keys) or `API_KEYS` env JSON

Marketplace (schema-compatible)
- List items: `GET /marketplace/items?category=...&status=active`
- Admin upsert: `POST /admin/marketplace/items?token=...` supports both payloads:
	- Legacy: `{code,title,description,price_usd,category,status}`
	- New: `{sku,title,type,price_usd}` (description/status via metadata)
- Purchase: `POST /marketplace/purchase` with `{item_code|item_id}` (requires API key/tenant)

Enterprise ops
- Seats: `GET /admin/seats?token=...&tenant_id=...`, `POST /admin/seats/upsert?token=...`
- Privacy: `GET /privacy/export` and `DELETE /privacy/delete` (header `X-User-Email` or `?email=`)
- Billing snapshot: `GET /admin/billing/snapshot?token=...&tenant_id=...`
- Watchlists (tenant-scoped):
	- `POST /watchlists` {name}
	- `GET /watchlists`
	- `POST /watchlists/{id}/items` {company_id, note?}
	- `DELETE /watchlists/{id}/items/{item_id}`

Admin plans/tenants/API keys
- Plans: `GET/POST/PUT/DELETE /admin/plans*?token=...`
- Tenants: `GET/POST /admin/tenants?token=...`
- API Keys: `GET/POST /admin/api-keys?token=...`

Webhooks
- Register/unregister (tenant-scoped) and durable delivery with backoff (in-memory or DB `webhook_queue`)
- Emit helper: `POST /admin/daas/emit-data-updated?token=...&tenant_id=`

Metrics
- Adds `aurora_tenants_total`, `aurora_active_seats_total`, `aurora_webhook_queue_depth`, marketplace/order/webhook gauges.

Environment
- `DEV_ADMIN_TOKEN`: enables /admin/* surfaces; pass `?token=...`
- `APIKEY_REQUIRED=1`: enforce API key middleware; header name `X-API-Key` (configurable)
- `API_KEYS`: JSON array fallback: `[{"key":"sk_...","tenant_id":"t1","scopes":["use:copilot"],"plan":"pro"}]`
- `DURABLE_WEBHOOKS=1`: enable background webhook worker (uses DB if available)

Migrations
- Apply Alembic migrations: `alembic upgrade head`
- New revisions:
	- `0006_phase4_tables`: tenants, api_keys, plans, subscriptions, usage_events, entitlement_overrides, marketplace_items, orders
	- `0007_phase4_enterprise_and_queue`: webhook_queue, org_seats, watchlists(+items), and marketplace back-compat columns

### Grafana dashboard (metrics)

- Import `docs/grafana/aurora-phase4-dashboard.json` into Grafana.
- Set the Prometheus datasource when prompted.
- Ensure Prometheus scrapes `/metrics` from the API service. Example scrape:
	- job_name: aurora
		metrics_path: /metrics
		static_configs:
			- targets: ['localhost:8000']

Panels include request totals, error rate, latency p50/p95/p99, webhook queue depth, marketplace/orders gauges, cache hit ratio, and usage units by product.


## Phase 5 — Sovereign Platform (quick reference)

Endpoints (admin endpoints require DEV_ADMIN_TOKEN):
- KG & Provenance: POST /kg/query, POST /admin/kg/snapshot, GET /provenance/bundle, GET /daas/kg/changed
- Agents: POST /admin/agents/start, GET /admin/agents/runs/{id}, PUT /admin/agents/runs/{id}, POST /admin/agents/memo/generate
- Deal rooms: POST /admin/deal-rooms, GET /admin/deal-rooms, POST /admin/deal-rooms/{id}/memos/attach,
  POST/GET/DELETE /admin/deal-rooms/{id}/comments, POST/GET/PUT/DELETE /admin/deal-rooms/{id}/checklist,
  GET /admin/deal-rooms/{id}/export?format=csv|ndjson
- Certification: POST /admin/certifications/upsert, GET /admin/certifications
- Success-fee pilot: POST/GET /admin/success-fee/agreements, POST /admin/success-fee/intro, POST /admin/success-fee/close
- Dev tools: POST /dev/memo/validate, POST /forecast/simulate

Metrics (added in Phase 5):
- aurora_kg_nodes_total, aurora_kg_edges_total, aurora_agents_running_total,
  aurora_certified_analysts_total, aurora_success_fee_agreements_total

Grafana:
- Import `docs/grafana/aurora-phase5-dashboard.json` and select the Prometheus datasource.

E2E smoke (admin):
1) Start agent: POST /admin/agents/start?token=... → id
2) Generate memo: POST /admin/agents/memo/generate?token=...
3) Create room: POST /admin/deal-rooms?token=...
4) Attach memo: POST /admin/deal-rooms/{id}/memos/attach?token=...
5) Export: GET /admin/deal-rooms/{id}/export?format=csv&token=...
6) Snapshot KG: POST /admin/kg/snapshot?token=...

