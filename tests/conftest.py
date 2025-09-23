from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, create_engine

# Force an in-process SQLite DATABASE_URL for any code that reads env before monkeypatch
os.environ.setdefault("DATABASE_URL", "sqlite:///./aurora.db")

# Create a lightweight SQLite DB for KG endpoint tests.
# Use a file-based DB to persist across connections during the test session.
TMP_DIR = Path(os.environ.get("PYTEST_TMP", ".")) / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = TMP_DIR / "kg_test.sqlite"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

# Create minimal schema used by the tests and endpoints under test
def _wait_for_postgres_if_configured():
    url = os.environ.get("DATABASE_URL", "").lower()
    if not url.startswith("postgresql"):
        return
    import time, socket, re
    m = re.search(r"@([^/:]+):(\d+)", url)
    host, port = (m.group(1), int(m.group(2))) if m else ("localhost", 5432)
    deadline = time.time() + 8
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except Exception:
            time.sleep(0.4)
    print(f"[tests] WARNING: Postgres not reachable at {host}:{port} before timeout; tests may fallback/skip", flush=True)

_wait_for_postgres_if_configured()
with ENGINE.connect() as conn:
    # Always drop and recreate temporal tables to avoid stale schemas (e.g. prior UNIQUE constraint on uid)
    conn.exec_driver_sql("DROP TABLE IF EXISTS kg_nodes;")
    conn.exec_driver_sql("DROP TABLE IF EXISTS kg_edges;")
    conn.exec_driver_sql(
        """
        CREATE TABLE kg_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NULL,
            uid TEXT NOT NULL,
            type TEXT,
            properties_json TEXT,
            valid_from TEXT,
            valid_to TEXT,
            provenance_id INTEGER NULL,
            created_at TEXT
        );
        """
    )
    conn.exec_driver_sql("CREATE INDEX ix_kg_nodes_uid ON kg_nodes(uid);")
    conn.exec_driver_sql(
        """
        CREATE TABLE kg_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NULL,
            src_uid TEXT,
            dst_uid TEXT,
            type TEXT,
            properties_json TEXT,
            valid_from TEXT,
            valid_to TEXT,
            provenance_id INTEGER NULL,
            created_at TEXT
        );
        """
    )
    # Minimal provenance tables for provenance bundle helper safety
    conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS provenance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingest_event_id TEXT NULL,
            snapshot_hash TEXT NULL,
            signer TEXT NULL,
            pipeline_version TEXT NULL,
            model_version TEXT NULL,
            evidence_json TEXT NULL,
            doc_urls_json TEXT NULL,
            created_at TEXT NULL
        );
        """
    )
    conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS kg_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            at_ts TEXT,
            snapshot_hash TEXT,
            signer TEXT NULL,
            signature TEXT NULL,
            signature_backend TEXT NULL,
            cert_chain_pem TEXT NULL,
            dsse_bundle_json TEXT NULL,
            rekor_log_id TEXT NULL,
            rekor_log_index INTEGER NULL,
            notes TEXT NULL,
            created_at TEXT NULL
        );
        """
    )


class _CompatSession:
    """Thin wrapper to accept raw SQL strings in exec() for compatibility."""

    def __init__(self, session: Session):
        self._s = session

    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc is not None:
                self._s.rollback()
        finally:
            self._s.close()
        # Do not suppress exceptions
        return False

    # Delegate commonly used methods
    def add(self, *args, **kwargs):
        return self._s.add(*args, **kwargs)

    def commit(self):
        return self._s.commit()

    def rollback(self):
        return self._s.rollback()

    def execute(self, *args, **kwargs):
        return self._s.execute(*args, **kwargs)

    def exec(self, query, params=None):
        from sqlalchemy import text as sql_text  # type: ignore
        # Prefer execute() which supports parameters across SQLAlchemy versions
        if isinstance(query, str):
            return self._s.execute(sql_text(query), params or {})
        if params:
            return self._s.execute(query, params)
        # Fall back to native exec when no params supplied
        try:
            return self._s.exec(query)
        except TypeError:
            return self._s.execute(query)


@contextmanager
def _test_get_session():
    s = Session(ENGINE)
    try:
        yield _CompatSession(s)
    finally:
        # Ensure closure if not already closed in __exit__ path
        try:
            s.close()
        except Exception:
            pass


# Monkeypatch get_session for both the db module and the FastAPI app module
try:
    import apps.api.aurora.db as dbmod  # type: ignore
    dbmod.get_session = _test_get_session  # type: ignore[attr-defined]
except Exception:
    pass

try:
    import apps.api.aurora.main as mainmod  # type: ignore
    mainmod.get_session = _test_get_session  # type: ignore[attr-defined]
except Exception:
    pass
