from typing import List, Dict
from sqlmodel import select
from .db import Company, get_session


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
            existing = s.exec(select(Company).where(Company.canonical_name == name)).first()
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
