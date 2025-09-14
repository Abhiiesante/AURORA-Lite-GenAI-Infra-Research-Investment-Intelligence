from __future__ import annotations

import pandas as pd
from sqlmodel import select
from sqlalchemy import text
from apps.api.aurora.db import get_session, NewsItem, Filing, Repo, init_db


def upsert_news(df: pd.DataFrame) -> int:
    init_db()
    count = 0
    with get_session() as s:
        for _, r in df.iterrows():
            url = (r.get("url") or "").strip()
            if not url:
                continue
            title = (r.get("title") or "").strip() or url
            published_at = r.get("published_at")
            rows_iter = s.exec(text("SELECT id FROM news_items WHERE external_id=:eid").bindparams(eid=url))
            rows = list(rows_iter) if rows_iter is not None else []
            row = rows[0] if rows else None
            existing = s.get(NewsItem, int(row[0])) if row else None
            if existing:
                existing.title = title or existing.title
                existing.url = url
                existing.published_at = published_at or existing.published_at
                s.add(existing)
            else:
                s.add(NewsItem(external_id=url, title=title, url=url, published_at=published_at))
            count += 1
        s.commit()
    return count


def upsert_filings(df: pd.DataFrame) -> int:
    init_db()
    count = 0
    with get_session() as s:
        for _, r in df.iterrows():
            url = (r.get("url") or "").strip()
            if not url:
                continue
            rows_iter = s.exec(text("SELECT id FROM filings WHERE external_id=:eid").bindparams(eid=url))
            rows = list(rows_iter) if rows_iter is not None else []
            row = rows[0] if rows else None
            existing = s.get(Filing, int(row[0])) if row else None
            if existing:
                existing.filed_at = r.get("filed_at") or existing.filed_at
                existing.form = r.get("form_type") or existing.form
                s.add(existing)
            else:
                s.add(Filing(external_id=url, filed_at=r.get("filed_at"), form=r.get("form_type"), url=url))
            count += 1
        s.commit()
    return count


def upsert_repos(df: pd.DataFrame) -> int:
    init_db()
    count = 0
    with get_session() as s:
        for _, r in df.iterrows():
            url = (r.get("repo_url") or "").strip()
            if not url:
                continue
            rows_iter = s.exec(text("SELECT id FROM repos WHERE repo_full_name = :name").bindparams(name=url))
            rows = list(rows_iter) if rows_iter is not None else []
            row = rows[0] if rows else None
            existing = s.get(Repo, int(row[0])) if row else None
            if existing:
                existing.stars = r.get("stars") or existing.stars
                s.add(existing)
            else:
                s.add(Repo(repo_full_name=url, stars=r.get("stars")))
            count += 1
        s.commit()
    return count
