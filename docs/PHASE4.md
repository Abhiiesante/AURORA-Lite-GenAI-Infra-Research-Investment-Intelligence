# Phase 4 — Monetization & Moat (Scaffold)

This document tracks the initial scaffold for Phase 4: tenants, API keys, plans, subscriptions, and usage events.

## Data model (added)
- tenants, api_keys, plans, subscriptions, usage_events, entitlement_overrides, marketplace_items, orders

## Plan configuration (example)
```json
{
  "pro": {"api_calls": 50000, "copilot_credits": 5000, "bulk_export": "none", "webhooks": true},
  "team": {"api_calls": 250000, "copilot_credits": 25000, "bulk_export": "weekly", "webhooks": true},
  "enterprise": {"api_calls": 2000000, "copilot_credits": 250000, "bulk_export": "daily", "webhooks": true, "sso": true}
}
```

You can also pass plans as an array or under a `plans` key:

```json
{"plans": [{"code": "pro", "entitlements": {"api_calls": 50000}}]}
```

Enable API keys (dev/local):
- Set env
  - APIKEY_REQUIRED=1
  - API_KEYS=[{"key":"dev123","tenant_id":"t1","scopes":["use:copilot"],"plan":"pro"}]
  - PLANS_JSON={"pro":{"api_calls":50000}}
- Optional: POST /dev/plans/reload?token=$DEV_ADMIN_TOKEN
- Inspect: GET /dev/auth/whoami

## Next endpoints (planned)
- /admin/tenants, /admin/api-keys, /admin/plans, /admin/subscriptions
  - Read-only endpoints: GET /admin/plans, /admin/tenants, /admin/api-keys (dev-token guarded)
  - CRUD added (dev-token guarded):
    - POST /admin/plans { code, entitlements, [name, price_usd, period] }
    - PUT /admin/plans/{code} { entitlements, [name, price_usd, period] }
    - DELETE /admin/plans/{code}
    - POST /admin/tenants { name, [status] }
    - POST /admin/api-keys { tenant_id, [key], [scopes], [rate_limit_per_min], [expires_at], [status] }
  - All admin endpoints require: token query param matching DEV_ADMIN_TOKEN.
- /usage (query/export)
- /daas/bulk, /daas/webhook

## Usage metering
- /copilot/ask enforces quotas when API keys are enabled and records 1 unit per call under the `copilot` product.
- GET /usage returns a simple per-tenant summary for the active period with {used, limit} by product.
- Forecast endpoints will be wired next to record/enforce appropriate units.

## Admin quickstart

1) Set `DEV_ADMIN_TOKEN` in env and restart the API.
2) Create a plan (in-memory + best-effort DB):

```bash
curl -X POST "http://localhost:8000/admin/plans?token=$DEV_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"pro","entitlements":{"api_calls":50000,"copilot_credits":5000}}'
```

3) Create a tenant:

```bash
curl -X POST "http://localhost:8000/admin/tenants?token=$DEV_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"acme"}'
```

4) Create an API key (response returns plaintext key once):

```bash
curl -X POST "http://localhost:8000/admin/api-keys?token=$DEV_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"1","scopes":["use:copilot"],"rate_limit_per_min":120}'
```

Note: DB operations are best-effort. If no DB, admin endpoints will return 501 for DB-backed actions.

Notes: All features are feature-flagged and additive; existing Phase 3 flows remain unchanged.
