from __future__ import annotations

import os
import pandas as pd
from sqlmodel import select
from apps.api.aurora.db import Company, get_session, init_db

CURATED_COMPANIES = os.getenv("CURATED_COMPANIES", "data/curated/companies.parquet")


def upsert_company_row(s, row: pd.Series) -> None:
    name = str(row.get("name") or "").strip()
    if not name:
        return
    canonical_id = str(row.get("canonical_id") or "").strip() or None
    canonical_name = str(row.get("canonical_name") or name).strip()
    existing = s.exec(select(Company).where(Company.canonical_name == canonical_name)).first()
    if existing:
        existing.canonical_id = existing.canonical_id or canonical_id
        existing.website = row.get("website") or existing.website
        existing.hq_country = row.get("country") or existing.hq_country
        existing.segments = row.get("segment") or existing.segments
        s.add(existing)
    else:
        s.add(
            Company(
                canonical_id=canonical_id,
                canonical_name=canonical_name,
                website=row.get("website"),
                hq_country=row.get("country"),
                segments=row.get("segment"),
            )
        )


def main() -> None:
    init_db()
    if not os.path.exists(CURATED_COMPANIES):
        print(f"Missing {CURATED_COMPANIES}")
        return
    df = pd.read_parquet(CURATED_COMPANIES)
    with get_session() as s:
        for _, r in df.iterrows():
            upsert_company_row(s, r)
        s.commit()
    print(f"Upserted {len(df)} companies into Postgres")


if __name__ == "__main__":
    main()
