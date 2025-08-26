from __future__ import annotations

import os
from datetime import datetime

from prefect import flow, task, get_run_logger

from flows.ingest_rss import main as ingest_rss
from flows.ingest_github import main as ingest_github
from flows.ingest_edgar import main as ingest_edgar
from flows.compute_weekly import compute_weekly


@task
def _ingest_all():
    # fire-and-forget style: each will no-op gracefully on errors
    try:
        ingest_rss()
    except Exception:
        pass
    try:
        ingest_github()
    except Exception:
        pass
    try:
        ingest_edgar()
    except Exception:
        pass


@flow(name="weekly_pipeline")
def weekly_pipeline():
    logger = get_run_logger()
    logger.info("Starting weekly pipeline at %s", datetime.utcnow().isoformat())
    _ingest_all()
    res = compute_weekly()
    logger.info("Weekly pipeline completed: %s", res)
    return res


if __name__ == "__main__":
    print(weekly_pipeline())
