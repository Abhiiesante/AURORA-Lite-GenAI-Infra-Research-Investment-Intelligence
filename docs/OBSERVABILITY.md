# Observability Guide

This guide shows what to expect from the observability surfaces and how to read them.

## Endpoints

- GET /metrics — Prometheus text format for scraping (latency p50/p95/p99, error rate, cache hit ratio, request totals, eval gauges)
- GET /dev/metrics — JSON diagnostics (sliding-window percentiles, errors, cache stats, simple SLO alerts)

## Example: /metrics (Prometheus excerpt)

```
# HELP aurora_request_total Total HTTP requests
# TYPE aurora_request_total counter
aurora_request_total 123

# HELP aurora_request_latency_p50_milliseconds 50th percentile request latency
# TYPE aurora_request_latency_p50_milliseconds gauge
aurora_request_latency_p50_milliseconds 420

# HELP aurora_request_latency_p95_milliseconds 95th percentile request latency
# TYPE aurora_request_latency_p95_milliseconds gauge
aurora_request_latency_p95_milliseconds 810

# HELP aurora_request_latency_p99_milliseconds 99th percentile request latency
# TYPE aurora_request_latency_p99_milliseconds gauge
aurora_request_latency_p99_milliseconds 1240

# HELP aurora_error_rate_ratio Error rate over sliding window
# TYPE aurora_error_rate_ratio gauge
aurora_error_rate_ratio 0.01

# HELP aurora_cache_hit_ratio Cache hit ratio
# TYPE aurora_cache_hit_ratio gauge
aurora_cache_hit_ratio 0.67
```

Note: Metric names may include additional gauges/counters for caches and evals depending on build and feature flags.

## Example: /dev/metrics (JSON excerpt)

```json
{
  "window_size": 50,
  "request_count": 918,
  "latency_ms": { "p50": 420, "p95": 810, "p99": 1240, "avg": 503 },
  "errors": { "count": 9, "rate": 0.018 },
  "cache": { "hits": 134, "misses": 62, "hit_ratio": 0.684 },
  "alerts": []
}
```

## Optional tracing (OpenTelemetry)

Set the following to emit spans to an OTLP collector:

- OTEL_EXPORTER_OTLP_ENDPOINT
- OTEL_EXPORTER_OTLP_HEADERS (e.g., Authorization=...,api-key=...)
- OTEL_SERVICE_NAME

Then use your collector’s UI (Tempo, Jaeger, etc.) to inspect request and endpoint spans.

## Grafana dashboard

- Import `docs/dashboards/aurora-lite-observability-grafana.json` into Grafana.
- It charts request totals, error rate, cache hit ratio, and latency p50/p95/p99.

## Prometheus quickstart

Add a scrape job to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: aurora-lite
    scrape_interval: 15s
    static_configs:
      - targets: ["localhost:8000"]
        labels:
          env: local
    metrics_path: /metrics
```

If running behind a reverse proxy, ensure /metrics is exposed and reachable from Prometheus.

## Screenshots (to add)

- [ ] /metrics excerpt in Prometheus UI
- [ ] /dev/metrics JSON example in a browser
- [ ] Grafana dashboard panel view

## Optional: run Prometheus + Grafana via Docker Compose

From `docs/`:

```powershell
docker compose -f docker-compose.observability.yml up -d
```

Then:
- Prometheus UI: http://localhost:9090
- Grafana UI: http://localhost:3001 (import the provided dashboard JSON)

## Quick smoke test

From repo root:

```powershell
python scripts/smoke_observability.py
```
