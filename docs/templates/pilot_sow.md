# Pilot Statement of Work (SOW)

Version: 0.1

Overview
- Objective: Validate AURORA KG+ v2 in a focused environment
- Duration: 4–6 weeks
- Stakeholders: Sponsor, Product Owner, Technical Lead

Scope
- Use cases: [list 2–3]
- Data sources: [GitHub, RSS, EDGAR, others]
- Environments: Dev (local), Staging (optional)
- Success metrics: Time-to-answer, Evidence quality, Snapshot verification

Deliverables
- Deployed API and Web (dev)
- Ingested sample dataset aligned to use cases
- Acceptance demo using docs/ACCEPTANCE.md checklist
- Signed snapshot with merkle_root and /metrics dashboard

Roles & Responsibilities
- Client: Data access, SMEs, decision maker
- Vendor: Implementation, support, training

Timeline (example)
- Week 1: Kickoff, environment setup, data mapping
- Week 2: Ingestion + KG proofing, run tests
- Week 3: API integration, Postman tests
- Week 4: Demo, acceptance, next steps

Assumptions
- Sample data can be shared under acceptable terms
- Rate limits and quotas are within reasonable bounds

Out of Scope
- Production SSO, full SLAs, multi-tenant billing

Commercials
- Fixed fee or T&M (specify)
- Payment schedule: 50/50 on kickoff/acceptance (example)

Risks & Mitigations
- Data access delays → simulated data
- Ambiguous success criteria → early alignment (this doc)

Acceptance Criteria
- All checklist items in docs/ACCEPTANCE.md pass in client context
- Snapshot signature verifies (HMAC or Sigstore structural)

Change Control
- Material scope changes require written approval
