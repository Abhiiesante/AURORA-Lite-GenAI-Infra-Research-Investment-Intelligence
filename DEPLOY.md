# Deploy (Free Tiers)

This repo is designed to run on free tiers:

- API: Render (free) or Fly.io
- Web: Vercel Hobby
- Postgres: Neon or Supabase free
- Qdrant: Cloud free tier (or local via Docker)
- Meilisearch: local Docker (or host a small instance)
- Neo4j: local Docker

## One-command local bring-up

Requires Docker Desktop:

```powershell
cd infra
docker compose up -d --build
```

API available at http://localhost:8000, Web at http://localhost:3000.

## Environment variables

Copy `apps/api/.env.example` to `.env` in `apps/api`, and `apps/web/.env.example` to `.env` in `apps/web` if you customize endpoints. Docker Compose passes sane defaults.

API required env (typical):

- DATABASE_URL
- QDRANT_URL
- MEILI_URL
- NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD
- OLLAMA_BASE_URL (if using local LLM)
- ALLOWED_ORIGINS
- SUPABASE_JWT_SECRET (optional; enables auth for POST /insights)

## Seed data and indexes

```powershell
# seed a demo company and RAG docs
Invoke-WebRequest -Method POST http://localhost:8000/health/seed | Select-Object -Expand Content
Invoke-WebRequest -Method POST http://localhost:8000/health/seed-rag | Select-Object -Expand Content
```

## CI secrets for deploy (GitHub Actions)

- VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID (optional automated Vercel deploy)
- RENDER_API_KEY and RENDER_SERVICE_ID (optional automated Render deploy)
- GITHUB_TOKEN (provided) for GHCR image publishing
- FLY_API_TOKEN (if using Fly)
- SUPABASE_JWT_SECRET (if gating /insights POST)

Example env matrix (API):

```
DATABASE_URL: postgresql+psycopg2://<user>:<pass>@<host>/<db>
QDRANT_URL: https://<qdrant>
MEILI_URL: https://<meili>
ALLOWED_ORIGINS: *
SUPABASE_JWT_SECRET: <secret>
```
- NEON connection string or SUPABASE POSTGRES_URL

## Render/Fly API deploy

- Build with Dockerfile at `apps/api/Dockerfile`.
- Set env vars: `DATABASE_URL`, `QDRANT_URL`, `MEILI_URL`, `NEO4J_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OLLAMA_BASE_URL` (optional if cloud LLM), `ALLOWED_ORIGINS`, `SUPABASE_JWT_SECRET` (optional).

Supabase JWT secret:

- In Supabase: Settings -> API -> JWT Secret. Copy the value into `SUPABASE_JWT_SECRET` for the API service.
- Clients calling POST /insights must send a Bearer token signed with this secret (HS256).

### Concrete free-tier example

API on Render (Free Web Service):

1) New Web Service -> Docker -> repo path `apps/api`.
2) Port 8000 (Render auto-detect). Health check: `/health`.
3) Env (example):

```
DATABASE_URL=postgresql+psycopg2://<neon_user>:<neon_pass>@<neon_host>/<neon_db>
QDRANT_URL=https://<your-qdrant>.cloud.qdrant.io
MEILI_URL=https://<your-meili-host>
NEO4J_URL=
NEO4J_USER=
NEO4J_PASSWORD=
OLLAMA_BASE_URL=
ALLOWED_ORIGINS=*
SUPABASE_JWT_SECRET=<from Supabase Settings -> API>
```

Web on Vercel (Hobby):

1) Import project -> set root to `apps/web`.
2) Env:

```
NEXT_PUBLIC_API_URL=https://<your-render-api>.onrender.com
```

Data services:

- Neon: create a database; get connection string; plug into DATABASE_URL (psycopg2 URI).
- Qdrant Cloud: free tier instance; use HTTPS endpoint for QDRANT_URL.
- Meilisearch: run small instance or use local during dev; for prod, point MEILI_URL to hosted endpoint.

## Vercel Web deploy

- Root is `apps/web`.
- Env: `NEXT_PUBLIC_API_URL` -> your API public URL.

## RAG eval in CI

- Weekly scheduled workflow `.github/workflows/ragas-weekly.yml` runs the eval gates via `scripts/ci/run_ragas_ci.py`. It persists artifacts and fails on threshold dips and >5% WoW regressions.
- To run locally: `python scripts/ci/run_ragas_ci.py` (requires API deps installed).
