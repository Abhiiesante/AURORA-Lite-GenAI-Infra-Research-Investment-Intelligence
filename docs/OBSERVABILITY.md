# Observability Guide

This guide shows what to expect from the observability surfaces and how to read them.

## Endpoints

- GET /metrics — Prometheus text format for scraping (latency p50/p95/p99, error rate, cache hit ratio, request totals, eval gauges)
- GET /dev/metrics — JSON diagnostics (sliding-window percentiles, errors, cache stats, simple SLO alerts)

## Example: /metrics (Prometheus excerpt)

```
# HELP aurora_hybrid_cache_hits Total hybrid cache hits
# TYPE aurora_hybrid_cache_hits counter
aurora_hybrid_cache_hits 10

# HELP aurora_hybrid_cache_misses Total hybrid cache misses
# TYPE aurora_hybrid_cache_misses counter
aurora_hybrid_cache_misses 5

# HELP aurora_hybrid_cache_size Hybrid cache size
# TYPE aurora_hybrid_cache_size gauge
aurora_hybrid_cache_size 7

# HELP aurora_docs_cache_hits Total doc cache hits
# TYPE aurora_docs_cache_hits counter
aurora_docs_cache_hits 12

# HELP aurora_docs_cache_misses Total doc cache misses
# TYPE aurora_docs_cache_misses counter
aurora_docs_cache_misses 3

# HELP aurora_docs_cache_size Doc cache size
# TYPE aurora_docs_cache_size gauge
aurora_docs_cache_size 4

# HELP aurora_requests_total Total HTTP requests
# TYPE aurora_requests_total counter
aurora_requests_total 123

# HELP aurora_request_latency_avg_ms Average request latency (ms)
# TYPE aurora_request_latency_avg_ms gauge
aurora_request_latency_avg_ms 503.00

# HELP aurora_request_errors_total Total HTTP error responses
# TYPE aurora_request_errors_total counter
aurora_request_errors_total 2

# HELP aurora_request_error_rate Error rate (0-1)
# TYPE aurora_request_error_rate gauge
aurora_request_error_rate 0.0163

# HELP aurora_hybrid_cache_hit_ratio Hybrid cache hit ratio (0-1)
# TYPE aurora_hybrid_cache_hit_ratio gauge
aurora_hybrid_cache_hit_ratio 0.6667

# HELP aurora_request_latency_p50_ms P50 latency (ms)
# TYPE aurora_request_latency_p50_ms gauge
aurora_request_latency_p50_ms 420.00

# HELP aurora_request_latency_p95_ms P95 latency (ms)
# TYPE aurora_request_latency_p95_ms gauge
aurora_request_latency_p95_ms 810.00

# HELP aurora_request_latency_p99_ms P99 latency (ms)
# TYPE aurora_request_latency_p99_ms gauge
aurora_request_latency_p99_ms 1240.00

# HELP aurora_usage_units_total Total usage units by product for current period
# TYPE aurora_usage_units_total counter
aurora_usage_units_total{product="forecast"} 9

# HELP aurora_kg_nodes_total Total KG nodes
# TYPE aurora_kg_nodes_total gauge
aurora_kg_nodes_total 0

# HELP aurora_kg_edges_total Total KG edges
# TYPE aurora_kg_edges_total gauge
aurora_kg_edges_total 0

# HELP kg_snapshot_hash_total Total snapshot hash computations
# TYPE kg_snapshot_hash_total counter
kg_snapshot_hash_total 0

# HELP kg_snapshot_sign_total Total snapshot sign attempts (create)
# TYPE kg_snapshot_sign_total counter
kg_snapshot_sign_total 0

# HELP kg_snapshot_verify_total Total snapshot verify attempts
# TYPE kg_snapshot_verify_total counter
kg_snapshot_verify_total 0
```

Note: Metric names include both aurora_* (requests, caches, usage, evals, KG counts) and Phase 6 kg_snapshot_* counters. Some lines may be absent if a feature is disabled or the backing store is unavailable (e.g., doc cache gauges in minimal builds).

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
