# Phase 2 Acceptance — How to verify

This guide enumerates the Phase 2 acceptance checks (M1–M10) and how to validate them locally.

Prereqs
- Python 3.11 venv
- `pip install -e .` (or `pip install -r requirements.txt`)
- Optional services (Qdrant/Meilisearch/Neo4j) are not required for tests; code degrades gracefully.

Smoke
- Run tests: `pytest -q`

Checks
1) M1 — Copilot v2
- POST /copilot/ask with a question returns { answer, sources[], citations[] } (when no session).
- Citations are enforced to be a subset of retrieved docs.

2) M2 — Dashboard and Trends
- GET /company/{id}/dashboard responds with KPIs + sparklines[].
- GET /trends/top and /trends/{topic_id} return topics and weekly series with change_flag.

3) M3 — Signals/Alerts
- GET /signal/{id} returns series; GET /alerts/{id} returns alert list.

4) M4 — Topics pipeline
- POST /topics/run triggers compute_topics; Topic/TopicTrend persisted when DB available; periodic refit via topic_refit_days.

5) M5 — Schedules
- /ingest/schedule stores a JobSchedule row when DB available; /ingest/status lists; /ingest/cancel cancels.

6) M6 — Field-level citations
- POST /compare returns narrative with inline `[source: ...]` and a sources[] list.
- POST /reports/build returns bullets ending with `[source: ...]`.

7) M7 — Graph
- /graph/ego/{id}, /graph/similar/{id} minimal responses; /market/graph shapes for UI.

8) M8 — Feeds + quality
- /feeds/seed adds curated feeds; /feeds/validate runs dedup (url_hash) and optional LSH; language and timestamp checks included.

9) M9 — Evals
- /evals/summary exposes metrics; /evals/run stores artifact retrievable via /evals/report/latest.

10) M10 — UX/perf
- /compare and /company/{id}/dashboard include ETag and honor If-None-Match (304).
- Web app includes ISR proxy for dashboard and client ETag-aware fetch helper.

UI
- /market-map, /trends, /compare, /dashboard available; basic UX complete.

Notes
- Heavy libs (BERTopic, ruptures, spaCy model, datasketch, langdetect) are optional; features degrade but contracts hold.
- DB migrations included (alembic 0001–0003). Run `alembic upgrade head` if using Postgres.
