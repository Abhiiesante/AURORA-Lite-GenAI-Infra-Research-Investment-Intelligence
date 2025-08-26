import os
import pandas as pd
import json
from pipelines.ingest.github_flow import github_flow

RAW_PARQUET = os.getenv("REPOS_PARQUET", "data/raw/repos.parquet")


def main():
    path = github_flow()
    rows = []
    if path and os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
            for r in data.get("items", []):
                rows.append({
                    "repo_url": r.get("html_url"),
                    "stars": r.get("stargazers_count"),
                    "forks": r.get("forks_count"),
                    "topics": r.get("topics"),
                    "last_commit_at": r.get("pushed_at")
                })
        except Exception:
            pass
    if rows:
        df = pd.DataFrame(rows)
        os.makedirs(os.path.dirname(RAW_PARQUET), exist_ok=True)
        df.to_parquet(RAW_PARQUET, index=False)
        print("Wrote", RAW_PARQUET, len(df))
        try:
            from flows.upsert_postgres import upsert_repos
            upserted = upsert_repos(df)
            print("Upserted Repos to Postgres:", upserted)
        except Exception as e:
            print("Postgres upsert skipped:", e)
    else:
        print("No GitHub rows parsed.")


if __name__ == "__main__":
    main()
