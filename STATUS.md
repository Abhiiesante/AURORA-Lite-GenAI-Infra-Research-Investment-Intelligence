# Project Status (as of 2025-09-15)

This document summarizes the current state of the project, recent deliverables, verification status, and the next actionable steps.

## Phase 5: Completed ✅
- Multi-tenant retrieval (Qdrant + Meilisearch): fixed filter quoting, ID collisions; added reset flags and smokes; migrated to Qdrant `query_points()` with fallback.
- Snapshot integrity and attestation: HMAC signing and Sigstore DSSE verification with issuer/identity policy and payload SHA256 checks; offline structural fallback for CI.
- Admin hardening: Disabled features return 404; mirrored success-fee behavior.
- New endpoint: `/admin/kg/snapshot/attest` plus offline Sigstore E2E script and CI workflow.
- Docs and CI updated accordingly.

## Phase 6: In Progress 🚧
- Time-travel KG APIs:
  - `/kg/node`, batch `/kg/nodes`, `/kg/find` (filters), `/kg/edges`, `/kg/stats` with pagination.
  - Cursor-based keyset pagination added to `/kg/find` and `/kg/edges` (descending by id), alongside legacy offset/limit for back-compat.
  - OpenAPI spec updated; smoke scripts and unit tests added.
- Snapshot subsystem extensions:
  - Deterministic snapshot hashing now augmented with optional `merkle_root` (in-memory Merkle tree) for future inclusion proofs (field added to create, sign, list responses; spec & docs updated).
  - Prometheus metrics endpoint `/metrics` exposes counters for hash/sign operations and verification including duration sums (`kg_snapshot_hash_total`, `kg_snapshot_sign_total`, etc.).
  - Tests updated to assert Merkle root stability and metrics presence.

## Stability and DX
- Import stability: `apps/api/aurora/main.py` reinforced (imports + lightweight stubs) to avoid import-time errors during tests.
- Optional deps guarded: `temporalio` in `agents/temporal/worker_example.py` and `pandas` in `flows/index_search.py` now wrapped with try/except to avoid editor errors when missing.

## Verification
- Full pytest suite under `tests/` is currently green (with a few skips where appropriate).
- Smokes for KG endpoints and Sigstore structural E2E are in place.
- RAG golden harness added and wired into CI.

## Next Steps
1. Replace helper stubs in `apps/api/aurora/main.py` with production implementations (tracing spans, entity detection, topic refresh) when ready.
2. If desired, add `pandas` (and `pyarrow`) to dev dependencies for smoother local runs of `flows/index_search.py`.
3. Continue Phase 6 endpoints hardening and widen test coverage for edge cases (empty results, large page sizes, cursor expiry).

---
Generated automatically on 2025-09-15.
