# Deploy: API Containers

## Quick local run

Build and run the production image for a quick smoke:

```bash
docker build -f apps/api/Dockerfile -t ytd-api:local .

docker run --rm -p 8000:8000 \
  -e DATABASE_URL="sqlite:////app/aurora.db" \
  -e ALLOWED_ORIGINS="*" \
  ytd-api:local
```

Open:
- http://127.0.0.1:8000/healthz
- http://127.0.0.1:8000/metrics

The image includes a `prestart.sh` hook which attempts Alembic upgrade when
`DATABASE_URL` is provided and Alembic is installed.

## Security-related envs

- `ALLOWED_ORIGINS` (CSV) for CORS; default `*`.
- `trusted_hosts` (CSV) to enable TrustedHostMiddleware.
- `security_headers_enabled` (bool) to toggle secure headers.
- `content_security_policy` to override default CSP for API responses.
- `hsts_enabled` and `hsts_max_age` to control HSTS.
- `request_max_body_bytes` to cap request size (default 2MB).

## Reverse proxy notes

When running behind a reverse proxy (Nginx, Caddy, Cloud), ensure:
- TLS termination is enabled so HSTS is effective.
- Forwarded headers (X-Forwarded-Proto, X-Forwarded-For) are preserved if needed.
- CORS is aligned with your web origin(s) and set via `ALLOWED_ORIGINS`.

