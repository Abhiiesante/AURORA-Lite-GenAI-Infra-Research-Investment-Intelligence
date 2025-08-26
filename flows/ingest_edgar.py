import os
import pandas as pd
from pipelines.ingest.edgar_flow import edgar_flow
import xml.etree.ElementTree as ET

RAW_PARQUET = os.getenv("FILINGS_PARQUET", "data/raw/filings.parquet")


def main():
    out = edgar_flow()
    path = out.get("path") if isinstance(out, dict) else None
    rows = []
    if path and os.path.exists(path):
        try:
            root = ET.parse(path).getroot()
            for item in root.findall(".//item"):
                title = item.findtext("title")
                link = item.findtext("link")
                pub = item.findtext("pubDate")
                rows.append({"title": title, "url": link, "filed_at": pub})
        except Exception:
            pass
    if rows:
        df = pd.DataFrame(rows)
        os.makedirs(os.path.dirname(RAW_PARQUET), exist_ok=True)
        df.to_parquet(RAW_PARQUET, index=False)
        print("Wrote", RAW_PARQUET, len(df))
        try:
            from flows.upsert_postgres import upsert_filings
            upserted = upsert_filings(df)
            print("Upserted Filings to Postgres:", upserted)
        except Exception as e:
            print("Postgres upsert skipped:", e)
    else:
        print("No EDGAR rows parsed.")


if __name__ == "__main__":
    main()
