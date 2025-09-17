# SOC 2 Readiness Matrix (Phase 6)

This checklist maps SOC 2 controls to product features, owners, and evidence artifacts.

- Control: Access Control
  - Feature: RBAC, API keys, tenant isolation
  - Owner: Eng
  - Evidence: config, code refs, audit logs, tests

- Control: Change Management
  - Feature: PR reviews, CI gates (RAG, perf), signed snapshots
  - Owner: Eng
  - Evidence: CI runs, docs/CI_GATES.md, signed snapshot records

- Control: Security Monitoring
  - Feature: OTel traces, Prometheus metrics, alerting
  - Owner: SRE
  - Evidence: Grafana dashboards, alert history, runbooks

- Control: Data Retention & Backups
  - Feature: LakeFS snapshots, DR plan
  - Owner: SRE
  - Evidence: backup logs, recovery drills

- Control: Vendor Management
  - Feature: Third-party inventory, DPA templates
  - Owner: Legal
  - Evidence: contracts, DPAs
