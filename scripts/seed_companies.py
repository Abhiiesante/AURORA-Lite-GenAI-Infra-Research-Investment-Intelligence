from __future__ import annotations

import csv
from pathlib import Path
from apps.api.aurora.db import get_session, init_db, Company


CSV_PATH = Path(__file__).resolve().parent / "companies.csv"


def seed() -> int:
    init_db()
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing CSV at {CSV_PATH}")
    with open(CSV_PATH, newline="", encoding="utf-8") as f, get_session() as s:
        rdr = csv.DictReader(f)
        count = 0
        for row in rdr:
            name = (row.get("canonical_name") or row.get("name") or "").strip()
            if not name:
                continue
            canonical_id = (row.get("company_id") or name.lower().replace(" ", "-")).strip()
            segments = row.get("segment") or row.get("segments") or None
            comp = Company(
                canonical_name=name,
                website=row.get("website"),
                hq_country=row.get("country"),
                segments=segments,
            )
            if hasattr(comp, "canonical_id"):
                try:
                    setattr(comp, "canonical_id", canonical_id)
                except Exception:
                    pass
            s.add(comp)
            count += 1
        s.commit()
        return count


if __name__ == "__main__":
    print(f"Seeded {seed()} companies")
