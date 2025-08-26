import os
import pandas as pd
from pipelines.ingest.rss_flow import rss_flow

RAW_PARQUET = os.getenv("NEWS_PARQUET", "data/raw/news_items.parquet")


def main():
    paths = rss_flow()
    # minimal consolidation: each path is JSON list of entries
    rows = []
    for p in paths:
        try:
            rows.extend(pd.read_json(p).to_dict(orient="records"))
        except Exception:
            pass
    if rows:
        df = pd.DataFrame(rows)
        os.makedirs(os.path.dirname(RAW_PARQUET), exist_ok=True)
        df.to_parquet(RAW_PARQUET, index=False)
        print("Wrote", RAW_PARQUET, len(df))
        try:
            from flows.upsert_postgres import upsert_news
            upserted = upsert_news(df)
            print("Upserted News to Postgres:", upserted)
        except Exception as e:
            print("Postgres upsert skipped:", e)


if __name__ == "__main__":
    main()
