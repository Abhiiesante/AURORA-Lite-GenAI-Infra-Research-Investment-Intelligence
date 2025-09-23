# Local Testing Guide

This repo includes a lightweight SQLite harness so most API tests can run without external services.

## One-time setup

- Python: Devcontainer uses Python 3.12 with a virtualenv at `.venv`.
- Install runtime dependencies:

```bash
/workspaces/YTD/.venv/bin/python -m pip install -r requirements.txt
```

- Optional developer extras (pandas/pyarrow):

```bash
/workspaces/YTD/.venv/bin/python -m pip install -r requirements-dev.txt
```

## Run the full test suite

```bash
/workspaces/YTD/.venv/bin/python -m pytest -q
```

## Run API basics and copilot tests

```bash
/workspaces/YTD/.venv/bin/python -m pytest -q \
  apps/api/tests/test_phase2_basics.py::test_ask_requires_citations \
  apps/api/tests/test_copilot_m1.py::test_copilot_ask_returns_strict_schema_and_citations
```

## Run RAG gates and metrics gate tests

```bash
/workspaces/YTD/.venv/bin/python -m pytest -q \
  apps/api/tests/test_m9_ci_gates_observability.py::test_rag_gate_pass_allowed_domain \
  apps/api/tests/test_phase5_realtime_verification.py::test_hybrid_cache_hits_and_misses_change_with_repeated_query
```

## Run KG endpoints cursor tests (SQLite)

These tests use an in-memory SQLite DB and a lightweight session wrapper via `tests/conftest.py`. No external DB is required.

```bash
/workspaces/YTD/.venv/bin/python -m pytest -q tests/test_phase6_kg_endpoints.py
```

## Run snapshot hashing/signing tests (admin + signing env)

Set required environment variables to enable the admin guarded tests and HMAC signing backend:

```bash
export DEV_ADMIN_TOKEN=devtoken
export SIGNING_BACKEND=hmac
export AURORA_SNAPSHOT_SIGNING_SECRET=test-secret
```

Then run the snapshot tests:

```bash
/workspaces/YTD/.venv/bin/python -m pytest -q apps/api/tests/test_phase6_snapshots.py
```

## Quick-start external services (optional)

Some tests are skipped by default because they require external services. You can spin them up locally with Docker and enable the tests via environment variables.

- Start services (Postgres, Meilisearch, Qdrant):

```bash
docker compose -f infra/docker-compose.yml up -d postgres meilisearch qdrant
```

- Set environment variables (new terminal session or export before running tests):

```bash
# Postgres for admin/DB flows
export DATABASE_URL='postgresql+psycopg://aurora:aurora@localhost:5432/aurora'
export DEV_ADMIN_TOKEN='devtoken'

# Retrieval services for tenant smoke tests
export AURORA_RUN_TENANT_SMOKE=1
export MEILI_URL='http://localhost:7700'
export QDRANT_URL='http://localhost:6333'
```

Notes:
- The API will auto-create SQLModel tables on first use when connected. If you prefer migrations, use Alembic (`alembic upgrade head`) with a configured DB URL.
- Keep Docker Desktop or your container runtime running while tests execute.
- To stop services: `docker compose -f infra/docker-compose.yml down` (data persists in volumes unless you add `-v`).

### Admin KG local smoke (optional)

Once Postgres is running and `DEV_ADMIN_TOKEN` is set, you can exercise admin KG upserts locally without HTTP tooling:

```bash
# Requires DATABASE_URL and DEV_ADMIN_TOKEN in your env
/workspaces/YTD/.venv/bin/python scripts/smoke_kg_admin_local.py
```

Alternatively, use the VS Code task “Smokes: KG (admin local)” or the Make target:

```bash
make smoke-kg-admin
```

## Troubleshooting

- If you see `ModuleNotFoundError: sqlmodel`, ensure dependencies are installed using the venv path above.
- Some tests are environment-dependent and may `skip` if external services are unavailable.
- Use `-k` to select tests by keyword and `-q` for concise output.

## Skips explained and how to enable them

Some tests are intentionally skipped in minimal local runs. Enable them with the appropriate environment variables and backing services.

- Tenant smoke retrieval tests
  - Why skipped: External services (Meilisearch/Qdrant) not available by default.
  - Enable by setting:
    - `AURORA_RUN_TENANT_SMOKE=1`
    - `MEILI_URL=http://localhost:7700` (or your Meilisearch URL)
    - `QDRANT_URL=http://localhost:6333` (or your Qdrant URL)
  - Ensure those services are running and accessible.

- Admin/DB-dependent tests (agents, dealrooms, KG admin flows, exports)
  - Why skipped: Require admin token and a writable DB with expected tables/migrations.
  - Enable by setting:
    - `DEV_ADMIN_TOKEN=your-dev-token`
  - And providing a backing database the API can connect to (e.g., Postgres) with migrations applied. If DB/admin endpoints aren’t available, these tests will skip rather than fail.

- Quota/marketplace/backtest tests
  - Why skipped or tolerant: Depend on API key mode and optional product plans configuration.
  - Typical env to exercise flows:
    - `APIKEY_REQUIRED=1`
    - `API_KEYS='[{"tenant_id":"1","key":"dev"}]'`
    - `PLANS_JSON='{"free":{"limits":{"forecast":100}}}'`
  - Many tests set these via `monkeypatch`; the above env is only needed when running endpoints outside those tests.

- Observability/metrics gates
  - These assert the presence of metrics families; some are opportunistic and will `skip` if metrics are not enabled in your environment.

Tip: list skip reasons with `-rs` for a concise summary.