from __future__ import annotations

import os
import pandas as pd
from sqlmodel import select
from sqlalchemy import text
from apps.api.aurora.db import Company, get_session, init_db

CURATED_COMPANIES = os.getenv("CURATED_COMPANIES", "data/curated/companies.parquet")


def upsert_company_row(s, row: pd.Series) -> None:
    name = str(row.get("name") or "").strip()
    if not name:
        return
    canonical_id = str(row.get("canonical_id") or "").strip() or None
    canonical_name = str(row.get("canonical_name") or name).strip()
    row_t = s.exec(
        text("SELECT id FROM companies WHERE canonical_name = :name"),
        {"name": canonical_name},
    ).first()
    if row_t:
        cid = int(row_t[0] if isinstance(row_t, (tuple, list)) else row_t)
        existing = s.get(Company, cid)
        if existing is not None:
            try:
                if getattr(existing, "canonical_id", None) is None and canonical_id:
                    setattr(existing, "canonical_id", canonical_id)
            except Exception:
                pass
            existing.website = row.get("website") or existing.website
            existing.hq_country = row.get("country") or existing.hq_country
            existing.segments = row.get("segment") or existing.segments
            s.add(existing)
    else:
        c = Company(
            canonical_name=canonical_name,
            website=row.get("website"),
            hq_country=row.get("country"),
            segments=row.get("segment"),
        )
        # set canonical_id if model supports it
        if hasattr(c, "canonical_id") and canonical_id:
            try:
                setattr(c, "canonical_id", canonical_id)
            except Exception:
                pass
        s.add(c)


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
