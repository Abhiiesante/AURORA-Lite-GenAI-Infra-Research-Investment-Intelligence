import os
import pandas as pd
from rapidfuzz import fuzz

COMPANIES_CSV = os.getenv("COMPANIES_CSV", "scripts/companies.csv")
NEWS_PARQUET = os.getenv("NEWS_PARQUET", "data/raw/news_items.parquet")
CURATED_NEWS = os.getenv("CURATED_NEWS", "data/curated/news_items.parquet")


def load_companies():
    if os.path.exists(COMPANIES_CSV):
        return pd.read_csv(COMPANIES_CSV)
    return pd.DataFrame(columns=["name", "website", "aliases", "segment", "country"])  


def main():
    if not os.path.exists(NEWS_PARQUET):
        print("Missing news parquet")
        return
    df = pd.read_parquet(NEWS_PARQUET)
    companies = load_companies()
    def resolve_company(title: str) -> list[int]:
        hits = []
        for _, row in companies.iterrows():
            score = fuzz.token_set_ratio(str(title), str(row.get("name")))
            if score >= 90:
                hits.append(row.get("company_id") or row.get("id") or 0)
        return hits
    df["company_ids"] = df["title"].apply(resolve_company)
    os.makedirs(os.path.dirname(CURATED_NEWS), exist_ok=True)
    df.to_parquet(CURATED_NEWS, index=False)
    print("Enriched rows:", len(df))


if __name__ == "__main__":
    main()
