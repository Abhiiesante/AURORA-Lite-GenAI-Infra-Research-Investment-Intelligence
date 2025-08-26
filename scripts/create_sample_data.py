import os
import pandas as pd


def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def write_news(path: str):
    ensure_dir(path)
    df = pd.DataFrame([
        {
            "source": "https://semianalysis.com/feed/",
            "url": "https://example.com/news/1",
            "published_at": "2025-01-01T00:00:00Z",
            "title": "ExampleAI raises a seed round",
            "clean_text": "ExampleAI announced a new seed round to build a vector database.",
            "company_ids": [],
            "segment_tags": ["vector_db"],
            "sentiment_score": 0.2,
        }
    ])
    df.to_parquet(path, index=False)


def write_filings(path: str):
    ensure_dir(path)
    df = pd.DataFrame([
        {
            "cik": "0000000000",
            "company_name": "ExampleAI Inc.",
            "form_type": "8-K",
            "filed_at": "2025-01-02T00:00:00Z",
            "clean_text": "Current report on funding event.",
            "company_id": 1,
        }
    ])
    df.to_parquet(path, index=False)


def write_repos(path: str):
    ensure_dir(path)
    df = pd.DataFrame([
        {
            "repo_url": "https://github.com/example/exampleai",
            "stars": 10,
            "forks": 2,
            "topics": ["vector-database", "llm"],
            "last_commit_at": "2025-01-03T00:00:00Z",
            "company_id": 1,
        }
    ])
    df.to_parquet(path, index=False)


def main():
    write_news(os.path.join("data", "raw", "news_items.parquet"))
    write_filings(os.path.join("data", "raw", "filings.parquet"))
    write_repos(os.path.join("data", "raw", "repos.parquet"))
    print("Sample data written to data/raw/*")


if __name__ == "__main__":
    main()
