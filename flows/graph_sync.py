import os
import pandas as pd
from datetime import datetime, timedelta
from neo4j import GraphDatabase


NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "aurora")

NEWS = os.getenv("NEWS_PARQUET", "data/raw/news_items.parquet")
FILINGS = os.getenv("FILINGS_PARQUET", "data/raw/filings.parquet")
REPOS = os.getenv("REPOS_PARQUET", "data/raw/repos.parquet")
COMPANIES_CSV = os.getenv("COMPANIES_CSV", "scripts/companies.csv")

# Optional graph enrichment inputs
PEOPLE_CSV = os.getenv("PEOPLE_CSV", "data/raw/people.csv")
ADVISORS_CSV = os.getenv("ADVISORS_CSV", "data/raw/advisors.csv")
INVESTMENTS_CSV = os.getenv("INVESTMENTS_CSV", "data/raw/investments.csv")
COINVEST_CSV = os.getenv("COINVEST_CSV", "data/raw/co_invest.csv")


def _read_df(path: str, cols: list[str]) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def compute_signal(news_df: pd.DataFrame, repos_df: pd.DataFrame, filings_df: pd.DataFrame) -> dict:
    # simplistic score: news last 90d count + stars/10 + recent filing bonus
    scores: dict[int, float] = {}
    now = datetime.utcnow()
    cutoff = now - timedelta(days=90)
    # news
    if not news_df.empty and "company_ids" in news_df.columns:
        news_df = news_df.copy()
        if "published_at" in news_df.columns:
            news_df["published_at"] = pd.to_datetime(news_df["published_at"].astype(str), errors="coerce")
        recent = news_df[news_df["published_at"] >= cutoff] if "published_at" in news_df.columns else news_df
        for _, row in recent.iterrows():
            cids = row.get("company_ids")
            if isinstance(cids, (list, tuple)):
                for cid in cids:
                    try:
                        cid_i = int(cid)
                    except Exception:
                        continue
                    scores[cid_i] = scores.get(cid_i, 0.0) + 1.0
    # repos
    if not repos_df.empty and "company_id" in repos_df.columns:
        agg = repos_df.groupby("company_id")["stars"].sum().fillna(0) / 10.0
        for cid_val, val in agg.items():
            try:
                cid_i = int(cid_val)  # type: ignore[arg-type]
            except Exception:
                continue
            scores[cid_i] = scores.get(cid_i, 0.0) + float(val)
    # filings
    if not filings_df.empty and "company_id" in filings_df.columns:
        filings_df = filings_df.copy()
        if "filed_at" in filings_df.columns:
            filings_df["filed_at"] = pd.to_datetime(filings_df["filed_at"].astype(str), errors="coerce")
            recent_f = filings_df[filings_df["filed_at"] >= cutoff]
        else:
            recent_f = filings_df
        if "company_id" in recent_f.columns:
            cids_series = recent_f["company_id"].dropna()
            cids = pd.to_numeric(cids_series, errors="coerce").dropna().astype(int).tolist()
            for cid in cids:
                scores[int(cid)] = scores.get(int(cid), 0.0) + 1.0
    # normalize 0..100
    if not scores:
        return {}
    mx = max(scores.values()) or 1.0
    return {cid: round(100.0 * val / mx, 2) for cid, val in scores.items()}


def run_graph_sync():
    driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
    news = _read_df(NEWS, ["url", "published_at", "company_ids", "sentiment_score", "title"])  # type: ignore
    filings = _read_df(FILINGS, ["cik", "form_type", "filed_at", "company_id"])  # type: ignore
    repos = _read_df(REPOS, ["repo_url", "stars", "topics", "last_commit_at", "company_id"])  # type: ignore
    companies = _read_df(COMPANIES_CSV, ["id", "name", "website", "segment", "country"])  # type: ignore

    scores = compute_signal(news, repos, filings)

    with driver.session() as s:
        # Upsert segments and companies
        for _, c in companies.iterrows():
            cid = int(c.get("id") or 0)
            name = c.get("name") or ""
            seg = c.get("segment") or "unknown"
            seg_id = f"segment:{seg}"
            comp_id = f"company:{cid or name}"
            s.run(
                """
                MERGE (seg:Segment {id:$sid}) SET seg.label=$slabel
                MERGE (c:Company {id:$cid})
                  SET c.label=$clabel, c.segment=$segment, c.website=$website, c.country=$country, c.signal_score=$score
                MERGE (seg)-[:OPERATES_IN]->(c)
                """,
                sid=seg_id, slabel=seg.replace("_", " ").title(),
                cid=comp_id, clabel=name, segment=seg, website=c.get("website"), country=c.get("country"),
                score=scores.get(cid, 0.0),
            )

        # News items and MENTIONED_IN
        if not news.empty:
            for idx, row in news.iterrows():
                nid = f"news:{idx}:{row.get('url')}"
                s.run(
                    """
                    MERGE (n:NewsItem {id:$nid})
                      SET n.url=$url, n.published_at=$published_at, n.sentiment=$sentiment, n.title=$title
                    """,
                    nid=nid, url=row.get("url"), published_at=row.get("published_at"), sentiment=row.get("sentiment_score"), title=row.get("title"),
                )
                for cid in (row.get("company_ids") or []):
                    comp_id = f"company:{cid}"
                    s.run(
                        """
                        MATCH (c:Company {id:$cid}), (n:NewsItem {id:$nid})
                        MERGE (c)-[:MENTIONED_IN]->(n)
                        """,
                        cid=comp_id, nid=nid,
                    )

        # Filings and FILED rel
        if not filings.empty:
            for idx, row in filings.iterrows():
                fid = f"filing:{row.get('cik')}:{idx}"
                s.run(
                    """
                    MERGE (f:Filing {id:$fid})
                      SET f.cik=$cik, f.form_type=$form_type, f.filed_at=$filed_at
                    """,
                    fid=fid, cik=row.get("cik"), form_type=row.get("form_type"), filed_at=row.get("filed_at"),
                )
                cid = row.get("company_id")
                if pd.notna(cid):
                    comp_id = f"company:{int(cid)}"
                    s.run(
                        """
                        MATCH (c:Company {id:$cid}), (f:Filing {id:$fid})
                        MERGE (c)-[:FILED]->(f)
                        """,
                        cid=comp_id, fid=fid,
                    )

        # Repos and LINKED_TO
        if not repos.empty:
            for idx, row in repos.iterrows():
                rid = f"repo:{row.get('repo_url')}"
                s.run(
                    """
                    MERGE (r:Repo {id:$rid})
                      SET r.url=$url, r.stars=$stars, r.topics=$topics, r.last_commit_at=$last_commit
                    """,
                    rid=rid, url=row.get("repo_url"), stars=row.get("stars"), topics=row.get("topics"), last_commit=row.get("last_commit_at"),
                )
                cid = row.get("company_id")
                if pd.notna(cid):
                    comp_id = f"company:{int(cid)}"
                    s.run(
                        """
                        MATCH (c:Company {id:$cid}), (r:Repo {id:$rid})
                        MERGE (c)-[:LINKED_TO]->(r)
                        """,
                        cid=comp_id, rid=rid,
                    )

        # People and worked_at
        people = _read_df(PEOPLE_CSV, ["person_id", "name", "company_id", "title", "start_date", "end_date"])  # type: ignore
        if not people.empty:
            for _, row in people.iterrows():
                pid = f"person:{row.get('person_id') or row.get('name')}"
                s.run(
                    """
                    MERGE (p:Person {id:$pid})
                      SET p.name=$name
                    """,
                    pid=pid, name=row.get("name"),
                )
                cid = row.get("company_id")
                if pd.notna(cid):
                    comp_id = f"company:{int(cid)}"
                    s.run(
                        """
                        MATCH (p:Person {id:$pid}), (c:Company {id:$cid})
                        MERGE (p)-[r:WORKED_AT]->(c)
                          SET r.title=$title, r.start_date=$start, r.end_date=$end
                        """,
                        pid=pid, cid=comp_id, title=row.get("title"), start=row.get("start_date"), end=row.get("end_date"),
                    )

        # Advisors
        advisors = _read_df(ADVISORS_CSV, ["person_id", "company_id", "role"])  # type: ignore
        if not advisors.empty:
            for _, row in advisors.iterrows():
                pid = f"person:{row.get('person_id')}"
                cid = row.get("company_id")
                if pd.notna(cid):
                    comp_id = f"company:{int(cid)}"
                    s.run(
                        """
                        MERGE (p:Person {id:$pid})
                        WITH p
                        MATCH (c:Company {id:$cid})
                        MERGE (p)-[r:ADVISES]->(c)
                          SET r.role=$role
                        """,
                        pid=pid, cid=comp_id, role=row.get("role"),
                    )

        # Investors and INVESTED_IN
        investments = _read_df(INVESTMENTS_CSV, ["investor_id", "investor_name", "company_id", "round", "date"])  # type: ignore
        if not investments.empty:
            for _, row in investments.iterrows():
                iid = f"investor:{row.get('investor_id') or row.get('investor_name')}"
                s.run(
                    """
                    MERGE (i:Investor {id:$iid})
                      SET i.label=$name
                    """,
                    iid=iid, name=row.get("investor_name"),
                )
                cid = row.get("company_id")
                if pd.notna(cid):
                    comp_id = f"company:{int(cid)}"
                    s.run(
                        """
                        MATCH (i:Investor {id:$iid}), (c:Company {id:$cid})
                        MERGE (i)-[r:INVESTED_IN]->(c)
                          SET r.round=$round, r.date=$date
                        """,
                        iid=iid, cid=comp_id, round=row.get("round"), date=row.get("date"),
                    )

        # Co-investor relationships per company
        coinv = _read_df(COINVEST_CSV, ["investor_a", "investor_b", "company_id"])  # type: ignore
        if not coinv.empty:
            for _, row in coinv.iterrows():
                a = f"investor:{row.get('investor_a')}"
                b = f"investor:{row.get('investor_b')}"
                cid = row.get("company_id")
                if pd.notna(cid):
                    s.run(
                        """
                        MATCH (ia:Investor {id:$a}), (ib:Investor {id:$b})
                        MERGE (ia)-[:CO_INVESTED {company_id:$cid}]->(ib)
                        """,
                        a=a, b=b, cid=int(cid),
                    )
    driver.close()


if __name__ == "__main__":
    run_graph_sync()
