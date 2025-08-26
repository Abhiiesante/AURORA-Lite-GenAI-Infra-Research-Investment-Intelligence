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