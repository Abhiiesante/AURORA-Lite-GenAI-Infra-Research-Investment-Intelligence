from typing import List, Dict, Optional
from sqlmodel import select
from sqlalchemy import text
from .db import Company, CompanyMetric, get_session


def upsert_companies_from_items(items: List[Dict]) -> int:
    """Minimal ETL: upsert companies parsed from ingest items.
    Looks for keys: canonical_name, website, hq_country, segments (list[str]).
    """
    count = 0
    with get_session() as s:
        for it in items:
            name = it.get("canonical_name")
            if not name:
                continue
            # Avoid type issues with attribute access on class by using raw SQL to get id, then s.get
            rows_iter = s.exec(text("SELECT id FROM companies WHERE canonical_name=:name").bindparams(name=name))
            rows_list = list(rows_iter) if rows_iter is not None else []
            row = rows_list[0] if rows_list else None
            existing = s.get(Company, int(row[0])) if row else None
            if existing:
                existing.website = it.get("website", existing.website)
                existing.hq_country = it.get("hq_country", existing.hq_country)
                segs = it.get("segments")
                if segs is not None:
                    existing.segments = ",".join(segs) if isinstance(segs, list) else str(segs)
                s.add(existing)
            else:
                segs = it.get("segments")
                comp = Company(
                    canonical_name=name,
                    website=it.get("website"),
                    hq_country=it.get("hq_country"),
                    segments=",".join(segs) if isinstance(segs, list) else segs,
                )
                s.add(comp)
            count += 1
        s.commit()
    return count


def upsert_company_metrics(items: List[Dict]) -> int:
    """Upsert weekly company metrics.
    Expected item keys: company_id (int) or canonical_id (str), week_start (YYYY-MM-DD),
    mentions, filings, stars, commits, sentiment, hiring, patents, signal_score (all optional numerics).
    """
    count = 0
    with get_session() as s:
        for it in items:
            # Resolve company_id if only canonical_id provided
            company_id: Optional[int] = it.get("company_id")
            if company_id is None and it.get("canonical_id"):
                rows_iter2 = s.exec(text("SELECT id FROM companies WHERE canonical_id=:cid").bindparams(cid=it["canonical_id"]))
                rows_list2 = list(rows_iter2) if rows_iter2 is not None else []
                row2 = rows_list2[0] if rows_list2 else None
                company_id = int(row2[0]) if row2 else None
            if not company_id:
                continue
            week_start = str(it.get("week_start") or "")
            if not week_start:
                continue
            # Try to find existing row
            try:
                rows_iter3 = s.exec(text("SELECT id FROM company_metrics WHERE company_id=:cid AND week_start=:ws").bindparams(cid=company_id, ws=week_start))
                rows_list3 = list(rows_iter3) if rows_iter3 is not None else []
                row_obj = rows_list3[0] if rows_list3 else None
            except Exception:
                row_obj = None
            row = s.get(CompanyMetric, int(row_obj[0])) if row_obj else CompanyMetric(company_id=company_id, week_start=week_start)
            # Assign available fields
            for key in ("mentions", "filings", "stars", "commits", "sentiment", "hiring", "patents", "signal_score"):
                if key in it and it[key] is not None:
                    try:
                        setattr(row, key, float(it[key]) if key not in ("mentions", "filings", "stars", "commits") else int(it[key]))
                    except Exception:
                        setattr(row, key, it[key])
            s.add(row)
            count += 1
        try:
            s.commit()
        except Exception:
            pass
    return count
