SHELL := /bin/bash

.PHONY: services-up services-down api test test-kg smoke-kg-admin

services-up:
	docker compose -f infra/docker-compose.yml up -d postgres meilisearch qdrant

services-down:
	docker compose -f infra/docker-compose.yml down

api:
	${PWD}/.venv/bin/python -m uvicorn apps.api.aurora.main:app --reload --host 127.0.0.1 --port 8000

test:
	${PWD}/.venv/bin/python -m pytest -q

test-kg:
	${PWD}/.venv/bin/python -m pytest -q tests/test_phase6_kg_endpoints.py

smoke-kg-admin:
	DEV_ADMIN_TOKEN=$${DEV_ADMIN_TOKEN} DATABASE_URL=$${DATABASE_URL} ${PWD}/.venv/bin/python scripts/smoke_kg_admin_local.py
