from __future__ import annotations

"""
Seed or update hiring/patents metrics for demo/testing.
Run: python scripts/seed_metrics_hiring_patents.py
"""

from datetime import date, timedelta
from sqlmodel import Session
from sqlalchemy import text
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `apps.*` can be imported when running this script directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from apps.api.aurora.db import engine, Company, CompanyMetric  # type: ignore
except Exception:
    # Fallback: also try adding apps/api to path explicitly
    API_DIR = ROOT / "apps" / "api"
    if str(API_DIR) not in sys.path:
        sys.path.insert(0, str(API_DIR))
    from aurora.db import engine, Company, CompanyMetric  # type: ignore


def seed():
    with Session(engine) as s:
        rows = list(s.exec(text("SELECT id, canonical_name FROM companies")))  # type: ignore[arg-type]
        if not rows:
            print("No companies found. Run scripts/seed_demo_data.py first.")
            return
        start = date.today() - timedelta(days=42)
        for rid in rows:
            cid = int(rid[0] if isinstance(rid, (tuple, list)) else getattr(rid, "id", 0))
            # 6 weeks of synthetic hiring/patents
            for w in range(6):
                ws = (start + timedelta(days=7 * w)).isoformat()
                hiring = max(0.0, 5.0 + (w - 3) * 2.0)
                patents = 0.0 if w < 4 else float(w - 3)
                try:
                    # Upsert pattern (parameterized)
                    # Use text() with explicit bind params and avoid .first() typing issues
                    rows_iter = s.exec(text("SELECT id FROM company_metrics WHERE company_id=:cid AND week_start=:ws").bindparams(cid=cid, ws=ws))  # type: ignore[arg-type]
                    rows_list = list(rows_iter) if rows_iter is not None else []
                    row = rows_list[0] if rows_list else None
                    if row:
                        _ = s.exec(text("UPDATE company_metrics SET hiring=:hiring, patents=:patents WHERE company_id=:cid AND week_start=:ws").bindparams(hiring=hiring, patents=patents, cid=cid, ws=ws))  # type: ignore[arg-type]
                    else:
                        s.add(CompanyMetric(company_id=cid, week_start=ws, mentions=0, filings=0, stars=0, commits=0, sentiment=0.0, hiring=hiring, patents=patents))
                except Exception:
                    continue
        s.commit()


if __name__ == "__main__":
    seed()
    print("Seeded hiring/patents metrics.")
