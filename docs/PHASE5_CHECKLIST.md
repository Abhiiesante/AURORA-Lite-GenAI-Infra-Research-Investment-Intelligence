## Phase 5 — Sovereign Platform Checklist (status)

Date: 2025-09-14

This checklist maps Phase 5 deliverables to their implementation status in this repo. Each item includes pointers to files/endpoints as evidence plus crisp next steps to reach the Phase 5 acceptance criteria.

Legend: [Done] implemented and exercised in code/tests; [In progress] partially implemented or behind feature flag; [Pending] not implemented yet.

### A. Sovereign Knowledge Graph (KG+)

- [Done] Temporal KG queries (time-travel by `at`)
  - Evidence: `POST/GET /kg/query?at=...` with temporal filters over `valid_from`/`valid_to` in `kg_nodes`/`kg_edges`.
    - Files: `apps/api/aurora/main.py` (kg_query), `apps/api/aurora/db.py` (KGNode, KGEdge)


[Done] Immutable provenance records & signed snapshots
  - Evidence: `POST /admin/kg/snapshot` computes deterministic `snapshot_hash` and optional HMAC signature; `GET /admin/kg/snapshots`; `POST /kg/snapshot/verify`; `POST /admin/kg/snapshot/attest` attaches DSSE bundle and Rekor metadata.
    - Files: `apps/api/aurora/main.py` (admin_kg_snapshot, kg_snapshot_verify, admin_kg_snapshot_attest), `apps/api/aurora/db.py` (KGSnapshot, ProvenanceRecord)
  - Updates: Pluggable signing backend added (HMAC default, optional Sigstore); snapshot records now store signature and backend; append-only `ingest_ledger` table records snapshot events.
  - Status: Sigstore verification implemented (full DSSE verify with policy + payload hash check) with offline structural fallback; CI E2E added (offline structural). Optional: keyless signing to Fulcio/Rekor can follow.
  - Ops notes:
    - Env: SIGNING_BACKEND=hmac|sigstore; HMAC requires AURORA_SNAPSHOT_SIGNING_SECRET
  - Sigstore envs: SIGSTORE_ENV=production|staging, SIGSTORE_VERIFY_IDENTITY, SIGSTORE_VERIFY_ISSUER, SIGSTORE_ALLOW_UNSAFE_POLICY=1, SIGSTORE_OFFLINE_FALLBACK=1
    - Admin endpoints require DEV_ADMIN_TOKEN (header X-Dev-Token)

- [In progress] Multi-source confidence/credibility scoring
  - Evidence: RAG hybrid scoring (vector + fuzzy keyword) with `vector_score`, `keyword_fuzz`, `hybrid_score` added to citations.
    - Files: `apps/api/aurora/rag_service.py` (answer_with_citations)
  - Gaps: No source trust calibration, per-source priors, or longitudinal credibility.
  - Next: Add per-source priors + calibration and persist per-document credibility.

- [In progress] Public KG (sanitized) + private tenant layer
  - Evidence: Multi-tenant scaffolding across many tables (`tenant_id` columns, API keys, usage/entitlements). `DAAS` changed feed: `GET /daas/kg/changed`.
    - Files: `apps/api/aurora/db.py` (Tenant, ApiKey, UsageEvent, etc.), `apps/api/aurora/main.py` (apikey middleware, daas endpoints)
  - Updates: `tenant_id` added to `kg_nodes` and `kg_edges`; admin upsert/close/list and `/kg/query` now enforce tenant scope when available via API key; back-compat when absent.
  - Gaps: Vector index not tenant-namespaced yet.
  - Next: Adopt per-tenant vector namespaces/collections for Qdrant and Meili.

### B. Autonomous Research Agents

- [Done] Scout agents (24/7 discovery pipeline) — foundations
  - Evidence: Prefect flows for RSS/EDGAR/GitHub ingestion; flow stubs gated by settings.
    - Files: `pipelines/ingest/rss_flow.py`, `pipelines/ingest/edgar_flow.py`, `pipelines/ingest/github_flow.py`, `apps/api/aurora/flows.py`

- [Pending] Qualification agents (investment filters, scorecards)
  - Evidence: Basic `compute_signal` and topic trends; no dedicated triage/scorecard agent.
    - Files: `apps/api/aurora/metrics.py`, `apps/api/aurora/trends.py`, `flows/graph_sync.py` (compute_signal)
  - Next: Add rule engine + classifier that emits standardized scorecards with provenance.

- [In progress] Memo agents (RAG → memo with citations)
  - Evidence: `POST /admin/agents/memo/generate` produces memo drafts with citations; schema validator `POST /dev/memo/validate`.
    - Files: `apps/api/aurora/main.py` (memo endpoints), `apps/api/aurora/rag_service.py`
  - Gaps: No JSON-schema enforcement at generation time; confidence is stubbed; no golden-set eval.
  - Next: Enforce JSON schema via structured output; add RAG faithfulness evaluation in CI.

- [In progress] Agent orchestration & audit trails
  - Evidence: `agent_runs` table + CRUD (`/admin/agents/*`); `AuditEvent` model used in metrics path; Prefect scaffolding.
    - Files: `apps/api/aurora/db.py` (AgentRun, AuditEvent), `apps/api/aurora/main.py` (agent runs), `apps/api/aurora/flows.py`
  - Gaps: No long-running orchestration (Temporal/Prefect Cloud) with retries in prod config; chain-of-custody view.

### C. Outcome Products

- [Done] Deal Rooms with workflow (comments, DD checklist, export)
  - Evidence: `DealRoom*` tables; endpoints for create/list, comments, checklist, CSV/NDJSON export; tests cover headers/CSV.
    - Files: `apps/api/aurora/db.py` (DealRoom, DealRoomItem, DealRoomComment, DDChecklistItem), `apps/api/aurora/main.py` (deal room endpoints), `tests/test_admin_export.py`

- [In progress] Forecast-as-a-Service (API + scenario-sim)
  - Evidence: `POST /forecast/simulate` + CI gates hitting forecast endpoints; SMAPE thresholds from env.
    - Files: `apps/api/aurora/main.py` (forecast_simulate), `scripts/ci_gates.py`, `.env.*`
  - Gaps: Model stack not using LightGBM/XGBoost with calibrated outputs in this repo.

- [Done] Data Licensing (DaaS: live feeds & snapshots)
  - Evidence: `GET /daas/kg/changed`; admin export endpoints across entities; webhook delivery with signing & durable queue.
    - Files: `apps/api/aurora/main.py` (daas_kg_changed, exports, webhook queue)

- [In progress] Success-Fee Pilot
  - Evidence: Agreements, intros, close, and summary endpoints with DB-backed + in-memory fallback; public certification status API.
    - Files: `apps/api/aurora/db.py` (SuccessFeeAgreement, IntroEvent, AnalystCertification), `apps/api/aurora/main.py` (success-fee endpoints)
  - Gaps: Contracting/legal + billing integration; production-grade reporting.

### D. Marketplace & Certification

- [Done] Report marketplace (admin upsert/list, CSV)
  - Evidence: `marketplace_items` table; admin/list endpoints and tests.
    - Files: `apps/api/aurora/db.py` (MarketplaceItem), `apps/api/tests/test_phase4_marketplace.py`, `apps/api/tests/test_phase4_admin_csv_content.py`

- [Done] AURORA Certified Analyst program (MVP)
  - Evidence: Upsert/list admin endpoints and public `GET /certifications/status`.
    - Files: `apps/api/aurora/main.py`, `apps/api/aurora/db.py`, `apps/api/tests/test_phase5_cert_and_fees.py`

### E. Enterprise-grade Confidentiality

- [Pending] On-prem / VPC deployment (formal offering)
- [Pending] Confidential compute (Nitro Enclaves / SGX)
- [Pending] Federated analytics & secure aggregation; DP guards
  - Evidence today: RBAC header roles; API key middleware; CORS; observability.
    - Files: `apps/api/aurora/auth.py`, `apps/api/aurora/main.py` (apikey middleware), `docs/OBSERVABILITY.md`, `docs/prometheus.yml`

### F. Research Lab & IP Engine

- [In progress] Proprietary signals & whitepapers
  - Evidence: Signals/time-series tooling (topics, alerts, compute_signal) and docs.
  - Gaps: Research publications, IP/patent scaffolding not in repo; out-of-band.

### 3. Knowledge Kernel — architecture & guarantees

- [Done] Immutable store: Parquet present; snapshot signing via HMAC (default) and Sigstore verification (optional) in place.
  - Files: `flows/ingest_rss.py`, `flows/er_embedding.py` (Parquet IO)

- [Done] KG layer: SQLModel temporal tables + Neo4j enrichment
  - Files: `apps/api/aurora/db.py` (KGNode/KGEdge with temporal fields), `flows/graph_sync.py` (Neo4j upserts)

- [Done] Provenance ledger (append-only records)
  - Files: `apps/api/aurora/db.py` (ProvenanceRecord), endpoints write provenance on upserts.

- [Done] Indexing & retrieval: Qdrant (vectors) + Meilisearch (keyword) hybrid
  - Files: `apps/api/aurora/rag_service.py`, `flows/index_search.py`, `.env.local.example` (QDRANT/MEILI)

- [In progress] Query API: GraphQL-lite + REST
  - Files: `apps/api/aurora/graphql.py` (test-oriented), `apps/api/aurora/main.py` wires POST `/graphql`.
  - Gaps: Full GraphQL schema with time-bound graph queries and auth.

- [In progress] Audit UI: provenance bundle API exists; UI view TBD
  - Files: `GET /provenance/bundle`, `apps/api/aurora/main.py`

### 4. Agents — safety & governance

- [In progress] Human-in-the-loop for impactful actions
  - Evidence: Admin-token gated endpoints; no automated contracting.
  - Gaps: Formal review/approval workflow UI; explicit “insufficient evidence” paths in all agents.

- [Pending] Sandboxing: runtime limits, token budgets, forced evidence checks

### 5. Monetization & Commercial Innovations

- [In progress] Subscriptions, API keys, usage metering/quotas
  - Files: `apps/api/aurora/db.py` (Plan, Subscription, UsageEvent), `apps/api/aurora/main.py` (apikey middleware, usage, webhooks)
  - Gaps: Billing provider integration; plan management UI; invoices.

- [In progress] Private deployments offering & pricing levers (contracts required)

### 6. Security, Privacy & Compliance

- [In progress] Security basics: CORS, API keys, basic RBAC, webhook signing, observability
  - Files: `apps/api/aurora/main.py` (CORS, signing, durable webhooks), `docs/OBSERVABILITY.md`, `docs/docker-compose.observability.yml`

- [Pending] SOC 2 Type II readiness, ISO 27001, GDPR program, EU AI Act scaffolding

### 7. Research & Model Strategy

- [In progress] Forecasts & evaluation gates
  - Evidence: Forecast endpoints, CI gates using SMAPE thresholds; scenario simulation API.
  - Gaps: Calibrated probabilistic ensemble (LightGBM/XGBoost) and XAI (SHAP/LIME) not present.

- [Pending] Custom LLM adapters (LoRA/fine-tune) and continuous learning loop

### 8. Ecosystem & Standards

- [In progress] Provenance/Interchange schemas
  - Evidence: Memo schema validator endpoint; provenance bundle shape.
  - Gaps: Published schemas/SDKs and partner consortium are out-of-repo.

- [Pending] Official SDKs (Python/TS/Java), browser extension, Excel add-in

### 9. GTM, Ops, Org, Fundraising, Legal, M&A (programmatic items)

- [Pending] These are largely non-code tracks; some foundations exist (marketplace, success-fee APIs). Execution is external to the repo.

### 10. KPIs & Dashboards

- [In progress] Observability & basic KPIs
  - Evidence: Prometheus/Grafana configs, CI gates, usage metrics.
  - Gaps: Comprehensive dashboards for Phase 5 KPIs (RAG faithfulness, forecast MAPE, SLA, SOC2 controls) not built here.

---

## Acceptance Criteria Tracking

- Sovereign KG with signed snapshots & time-travel
  - Status: Done — endpoints exist; verification includes Sigstore DSSE (full) and CI structural E2E.

- Autonomous agents produce memos with RAG faithfulness ≥ 0.92 on golden set
  - Status: Pending — add golden set, evaluator, and CI gate; enforce structured outputs.

- Deal Rooms used by paying customers to close at least one pilot-originated deal
  - Status: Pending — success-fee endpoints exist; need live deployment + pilot evidence.

- Marketplace with 50 curated reports, revenue captured
  - Status: Pending — marketplace endpoints exist; requires onboarding + payments.

- Confidential compute/federated mode tested with enterprise client
  - Status: Pending.

- SOC 2 Type II readiness (controls implemented; audit started)
  - Status: Pending — needs policy, tooling, evidence collection outside code.

---

## High-impact next steps (implementation)

1) Hard provenance & signing
  - Added `/admin/kg/snapshot/attest` to attach DSSE bundle and Rekor metadata to snapshots.
  - CI verification path added using `/kg/snapshot/verify` (Sigstore structural offline).

2) Tenant isolation for KG and vectors
  - Completed: tenant_id in KG tables; enforced in admin/query endpoints.
  - Next: Per-tenant Qdrant/Meili collections or prefixes.

### New environment variables

- SIGNING_BACKEND=hmac|sigstore (default: hmac)
- AURORA_SNAPSHOT_SIGNING_SECRET=... (required for hmac backend)

3) Agentization & safety
   - Promote Prefect flows to durable orchestration; add retries/timeouts and budget limits.
   - Enforce JSON schemas at generation time; implement “insufficient evidence” fallback everywhere.

4) Forecasting upgrade
   - Implement calibrated ensemble (XGBoost/LightGBM) with SMAPE/CRPS metrics and SHAP explanations; wire CI gates.

5) Confidential & compliance path
   - Add enclave execution option for sensitive inference; draft SOC 2 control mappings and logging coverage.

6) Standards & SDKs
   - Publish Provenance & Memo JSON Schemas; add minimal Python/TypeScript SDKs (client + examples).

---

## Quality gates (quick triage)

- Build/Lint: N/A in this pass (docs-only). No code edits made.
- Unit tests: Not executed in this change. Repo contains Phase 5 tests (e.g., `apps/api/tests/test_phase5_*`).
- Smoke: N/A.

## Requirements coverage

- KG time-travel, provenance, and snapshots: Done for Phase 5 scope (tenant partitioning, HMAC signing, Sigstore verification, CI structural E2E).
- Agents (scout/memo) and audit trail: In progress (scout/memo present; qualifier pending; safety hardening pending).
- Outcome products (deal rooms, forecast, DaaS, success-fee): Mostly done at MVP level; forecasting/modeling depth pending.
- Marketplace & certification: Done (MVP endpoints); onboarding/payments pending.
- Confidentiality/compliance: Pending.
- Standards/SDKs: Pending.
