from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, create_engine

# Create a lightweight SQLite DB for KG endpoint tests.
# Use a file-based DB to persist across connections during the test session.
TMP_DIR = Path(os.environ.get("PYTEST_TMP", ".")) / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = TMP_DIR / "kg_test.sqlite"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

# Create minimal schema used by the tests and endpoints under test
with ENGINE.connect() as conn:
    conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS kg_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NULL,
            uid TEXT NOT NULL UNIQUE,
            type TEXT,
            properties_json TEXT,
            valid_from TEXT,
            valid_to TEXT,
            provenance_id INTEGER NULL,
            created_at TEXT
        );
        """
    )
    conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS kg_edges (
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
