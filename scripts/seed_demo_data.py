from __future__ import annotations

"""
Seed demo companies and weekly metrics so /compare can use real values locally.
Run: python scripts/seed_demo_data.py
"""

from datetime import date, timedelta
from sqlmodel import Session
from sqlalchemy import text

try:
    from apps.api.aurora.db import engine, Company, CompanyMetric  # type: ignore
except Exception:
    from aurora.db import engine, Company, CompanyMetric  # type: ignore


def seed():
    with Session(engine) as s:
        # Create companies if not exist
        pine = s.exec(text("SELECT id FROM companies WHERE canonical_name='Pinecone'"))  # type: ignore[arg-type]
        pine = pine.first() if pine is not None else None
        weav = s.exec(text("SELECT id FROM companies WHERE canonical_name='Weaviate'"))  # type: ignore[arg-type]
        weav = weav.first() if weav is not None else None
        if not pine:
            s.exec(text(
                """
                INSERT INTO companies(canonical_name, name, segments, website, hq_country, signal_score)
                VALUES ('Pinecone', 'Pinecone', 'Vector DB', 'https://www.pinecone.io', 'US', 55)
                """
            ))  # type: ignore[arg-type]
        if not weav:
            s.exec(text(
                """
                INSERT INTO companies(canonical_name, name, segments, website, hq_country, signal_score)
                VALUES ('Weaviate', 'Weaviate', 'Vector DB', 'https://weaviate.io', 'NL', 53)
                """
            ))  # type: ignore[arg-type]
        s.commit()

        # Re-fetch IDs
        pine_id_row = s.exec(text("SELECT id FROM companies WHERE canonical_name='Pinecone'"))  # type: ignore[arg-type]
        pine_id_row = pine_id_row.first() if pine_id_row is not None else None
        weav_id_row = s.exec(text("SELECT id FROM companies WHERE canonical_name='Weaviate'"))  # type: ignore[arg-type]
        weav_id_row = weav_id_row.first() if weav_id_row is not None else None
        pine_id = int(pine_id_row[0] if isinstance(pine_id_row, (tuple, list)) else pine_id_row) if pine_id_row is not None else 0
        weav_id = int(weav_id_row[0] if isinstance(weav_id_row, (tuple, list)) else weav_id_row) if weav_id_row is not None else 0

        # Insert last 4 weeks of metrics
        start = date.today() - timedelta(days=21)
        for w in range(4):
            ws = (start + timedelta(days=7 * w)).isoformat()
            # Pinecone a bit higher mentions, Weaviate higher commits
            s.add(CompanyMetric(company_id=pine_id, week_start=ws, mentions=5 + w, filings=0, stars=150 + 3 * w, commits=20 + w, sentiment=0.15, signal_score=55 + w))
            s.add(CompanyMetric(company_id=weav_id, week_start=ws, mentions=4 + w, filings=1 if w % 2 == 0 else 0, stars=145 + 4 * w, commits=22 + 2 * w, sentiment=0.12, signal_score=53 + w))
        s.commit()


if __name__ == "__main__":
    seed()
    print("Seeded demo data.")
