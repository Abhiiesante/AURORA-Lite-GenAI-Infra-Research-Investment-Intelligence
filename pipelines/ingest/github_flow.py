from prefect import flow, task
from typing import Any, cast
import requests
import os
from datetime import datetime
import json

DATA_DIR = os.environ.get("DATA_DIR", "/data")
GITHUB_URL = "https://api.github.com/search/repositories?q=topic:vector-database&sort=stars&order=desc&per_page=10"

@task
def fetch_repos(url: str):
    r = requests.get(url, timeout=30, headers={"Accept": "application/vnd.github+json"})
    r.raise_for_status()
    return r.json()

@task
def persist(payload: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(DATA_DIR, f"github_vector_db_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return path

@flow
def github_flow():
    data = cast(Any, fetch_repos)(GITHUB_URL)
    return cast(Any, persist)(data)

if __name__ == "__main__":
    print(github_flow())
