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

---

# Phase 6 Acceptance — How to verify

This section enumerates the Phase 6 checks (KG+ v2 and snapshot subsystem) and how to validate them locally.

Prereqs
- Python venv and dependencies installed (`requirements.txt`).
- Optional: Postgres via Docker compose.
- Set envs for admin and signing when exercising snapshot flows:
	- `export DEV_ADMIN_TOKEN=devtoken`
	- `export AURORA_SNAPSHOT_SIGNING_SECRET=test-secret`
	- `export SIGNING_BACKEND=hmac` (or leave unset for unsigned snapshots)

Minimal KG time-travel checks (SQLite)
- Run: `/workspaces/YTD/.venv/bin/python -m pytest -q tests/test_phase6_kg_endpoints.py`

Snapshot hashing, signing, verification, and metrics
- Start API (VS Code task: “API: Run (uvicorn)”).
- Create a snapshot:
	- `curl -s -X POST "http://127.0.0.1:8000/admin/kg/snapshot?token=$DEV_ADMIN_TOKEN" | jq`
	- Expect fields: `snapshot_hash`, `merkle_root` (nullable), `node_count`, `edge_count`, optional `signature`.
- Sign snapshot:
	- `curl -s -X POST http://127.0.0.1:8000/admin/kg/snapshot/sign?token=$DEV_ADMIN_TOKEN -H 'content-type: application/json' -d '{"snapshot_hash":"<hash>"}' | jq`
- Verify signature (body):
	- `curl -s -X POST http://127.0.0.1:8000/kg/snapshot/verify -H 'content-type: application/json' -d '{"snapshot_hash":"<hash>","signature":"<sig>"}' | jq`
- Verify signature (path variant):
	- `curl -s -X POST http://127.0.0.1:8000/kg/snapshot/<hash>/verify -H 'content-type: application/json' -d '{"signature":"<sig>"}' | jq`
- List snapshots (admin):
	- `curl -s "http://127.0.0.1:8000/admin/kg/snapshots?token=$DEV_ADMIN_TOKEN&limit=5" | jq`
- Metrics exposure:
	- `curl -s http://127.0.0.1:8000/metrics | grep kg_snapshot`

Optional Sigstore structural verify
- Set `SIGNING_BACKEND=sigstore` and supply a DSSE bundle with `payloadSHA256` matching the snapshot hash to `/kg/snapshot/verify`.

Artifacts
- OpenAPI: `specs/kg_plus_v2_openapi.yaml` — Phase 6 endpoints (snapshot create/sign/attest/verify/list, metrics).
- Docs: `docs/PHASE6_SOVEREIGN_ECOSYSTEM.md` — design and operational notes including Merkle root (5.3.4).
- Tests: `apps/api/tests/test_phase6_snapshots.py`, `tests/test_phase6_kg_endpoints.py`.

## Phase 6 Acceptance Checklist (operator view)

Prereqs
- [ ] Python env ready and dependencies installed
- [ ] API running locally (VS Code task "API: Run (uvicorn)")
- [ ] Optional: Postgres/Meili/Qdrant via "Services: Up" task (not required for basic checks)
- [ ] Env set (for snapshot flows): `DEV_ADMIN_TOKEN`, `SIGNING_BACKEND=hmac`, `AURORA_SNAPSHOT_SIGNING_SECRET`

KG Time-travel & Pagination
- [ ] GET `/kg/node/{id}?as_of=...` returns node with neighbor expansion when `depth>0`
- [ ] GET `/kg/edges?uid=...&as_of=...&limit=...` returns `next_offset` when more results exist
- [ ] GET `/kg/find?...&limit=...` returns `next_offset` and respects filters

Snapshot Lifecycle
- [ ] POST `/admin/kg/snapshot` returns JSON with `snapshot_hash` and (nullable) `merkle_root`; `node_count`/`edge_count` present
	- Quick check: `curl -s -X POST "http://127.0.0.1:8000/admin/kg/snapshot?token=$DEV_ADMIN_TOKEN" | jq`
- [ ] POST `/admin/kg/snapshot/sign` returns `{snapshot_hash, signature?, signature_backend?, signer?, regenerated, merkle_root?}`
- [ ] POST `/kg/snapshot/verify` with signature returns `{valid: true, backend: "hmac"}`
- [ ] POST `/kg/snapshot/{hash}/verify` (path variant) also returns `{valid: true}` when signature is valid
- [ ] GET `/admin/kg/snapshots` lists recent snapshots and includes `merkle_root` field (nullable)

Metrics & Observability
- [ ] GET `/metrics` exposes counters: `kg_snapshot_hash_total`, `kg_snapshot_sign_total`, durations, and verify totals/invalids
	- Quick check: `curl -s http://127.0.0.1:8000/metrics | grep kg_snapshot`

OpenAPI Contract
- [ ] `specs/kg_plus_v2_openapi.yaml` includes `merkle_root` in snapshot create/sign/list schemas; `/metrics` path present

Documentation
- [ ] `docs/PHASE6_SOVEREIGN_ECOSYSTEM.md` includes 5.3.4 Merkle root section and an endpoints overview under 5.2
- [ ] `docs/ACCEPTANCE.md` (this file) includes Phase 6 acceptance steps and checklist
- [ ] `docs/TESTING.md` includes snapshot test env setup and run instructions
- [ ] `STATUS.md` reflects Phase 6 enhancements (merkle_root + metrics)
- [ ] `README.md` contains Phase 6 quickstart and links to artifacts

Tests (local)
- [ ] `tests/test_phase6_kg_endpoints.py` passes (SQLite harness)
- [ ] `apps/api/tests/test_phase6_snapshots.py` passes when env vars set

Deferred (Informational only — not required to pass Phase 6)
- [ ] Sigstore keyless + Rekor inclusion proofs (to be implemented)
- [ ] LakeFS commit binding for snapshot lineage (to be implemented)
- [ ] Inclusion-proof endpoint for Merkle trees (to be implemented)
