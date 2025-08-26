# AURORA-Lite PRD (Phase 0)

This document captures the Phase 0 scope from the North-Star mandate provided.

## 1. Vision & Outcomes
- Outcome 1: Continuous ingestion with lineage and proofs.
- Outcome 2: RAG-backed investor briefs with open/local models only.
- Outcome 3: Interactive market map and public read API on free hosting.

## 2. Personas
- Student-Analyst, Hiring Manager/VC, Builder

## 3. In-Scope (MVP+)
- Sources: RSS, SEC/EDGAR, GitHub, CSV/Sheets
- Capabilities: Entity resolution, knowledge graph, vector search, RAG Q&A, auto-reports with citations, React frontend, public REST/GraphQL, deploy free

## 4. Non-Functional
- Availability: 99.5% UI, best-effort API
- Latency: P95 ≤ 500ms cached reads, ≤ 2s heavy reads, ≤ 12s long-form generations
- Freshness: Hourly news/filings, daily repos
- Security: Zero-trust basics, RBAC, encryption where available
- Observability: Free SaaS tiers or local

## 5. Success Metrics (OKRs)
- O1: 2-week demo: ingest → KG → RAG report → UI
- O2: ≥100 companies, ≥500 relationships, ≥50 tagged docs with citations
- O3: 1 flagship brief, 500+ views, 5+ recruiter/VC engagements

## 6. Architecture Overview
See `docs/architecture.md` for diagrams and data flows.

## 7. Initial Schema & Taxonomy
Entities: Company, Product, FundingRound, Repo, Filing, NewsItem, Segment, RiskSignal

Rels: COMPANY–BUILDS→PRODUCT, COMPANY–RAISED→FUNDINGROUND, COMPANY–MENTIONED_IN→NEWSITEM, COMPANY–OPERATES_IN→SEGMENT, COMPANY–LINKED_TO→REPO, COMPANY–FLAGGED_BY→RISKSIGNAL

Company fields: canonical_name, aliases[], website, hq_country, headcount_est, funding_total, last_round, last_round_date, repos[], sentiment_30/90, sources[]

## 8. Phase Exit Criteria
- PRD + OKRs + NFRs in repo
- Diagrams in /docs
- Docker Compose brings up core services
- Prefect flow ingests RSS + SEC → Parquet + Postgres
- LlamaIndex RAG answers with citations
- UI renders market map and profiles
- CI green: tests + GE checks + RAG eval
