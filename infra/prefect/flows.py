from __future__ import annotations

"""Minimal Prefect 2.x wrappers around existing scripts.
These tasks call into the current flows so we don't duplicate logic.
Optional: install `prefect` to run these locally or with an agent.
"""

from prefect import flow, task


@task
def ingest_rss_task():
    from flows.ingest_rss import main as rss_main

    rss_main()


@task
def ingest_edgar_task():
    from flows.ingest_edgar import main as edgar_main

    edgar_main()


@task
def ingest_github_task():
    from flows.ingest_github import main as gh_main

    gh_main()


@task
def er_embedding_task():
    from flows.er_embedding import main as er_main

    er_main()


@task
def index_search_task():
    from flows.index_search import main as index_main

    index_main()


@task
def graph_sync_task():
    from flows.graph_sync import run_graph_sync

    run_graph_sync()


@task
def data_contracts_check_task():
    from flows.data_contracts_check import main as dc_main

    dc_main()


@flow(name="daily_pipeline")
def daily_pipeline():
    """End-to-end orchestrated pipeline (demo):
    - Ingest -> ER -> Index -> Graph -> Data contracts
    """
    ingest_rss_task()
    ingest_edgar_task()
    ingest_github_task()
    er_embedding_task()
    index_search_task()
    graph_sync_task()
    data_contracts_check_task()


if __name__ == "__main__":
    daily_pipeline()
