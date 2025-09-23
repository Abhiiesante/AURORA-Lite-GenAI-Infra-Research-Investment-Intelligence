# Outcome-based Fee Structure (Template)

Version: 0.1

Context
- Pilot goal: [e.g., reduce time-to-insight by 50%]
- KPI baseline: [current value]
- KPI target: [target value]

Structure
- Fixed base fee: $X (covers setup + support)
- Success fee: $Y due upon demonstrating KPI target in acceptance session
- Optional bonus: $Z for stretch KPI > target by N%

Measurement
- Evidence via CI gates and /metrics
- RAG harness and golden set alignment (tests/rag_golden_set.json)
- Signed snapshot with merkle_root to attest data/state

Governance
- Weekly check-in: progress vs. KPI
- Final acceptance using docs/ACCEPTANCE.md

Exclusions
- Third-party infra costs (LlamaIndex models, DB, search infra)
- Data vendor fees

Termination
- Either party may terminate with 7 days written notice; fees pro-rated

Notes
- Replace placeholders with client-specific numbers and KPIs
