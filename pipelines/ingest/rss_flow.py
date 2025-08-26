from prefect import flow, task
import feedparser
import os
from datetime import datetime
import json

DATA_DIR = os.environ.get("DATA_DIR", "/data")

@task
def fetch_feed(url: str):
    return feedparser.parse(url)

@task
def persist(entries, feed_name: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(DATA_DIR, f"rss_{feed_name}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)
    return path

@flow
def rss_flow():
    feeds = {
        "semi-analysis": "https://semianalysis.com/feed/",
        "arxiv_ai": "https://export.arxiv.org/rss/cs.AI"
    }
    saved = []
    for name, url in feeds.items():
        parsed = fetch_feed(url)
        entries = [
            {"title": e.get("title"), "link": e.get("link"), "published": e.get("published", ""), "summary": e.get("summary", ""), "source": url}
            for e in parsed.entries
        ]
        saved.append(persist(entries, name))
    return saved

if __name__ == "__main__":
    print(rss_flow())
