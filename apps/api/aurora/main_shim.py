"""Shim so tests importing `aurora.main` resolve to the app.

This module provides a stable import surface for tests that expect
`aurora.main` while the real code lives under `apps.api.aurora.main`.
Some private helpers may not exist in all builds; import them lazily and
fallback to the public retrieval.hybrid when absent.
"""

from apps.api.aurora.main import app, settings, _DOCS, _ensure_citations

# Optional private helpers; tolerate absence in minimal builds
try:  # pragma: no cover - import guard
    from apps.api.aurora.main import _rrf_fuse as rrf_fuse, _bm25_like, _dense_like  # type: ignore
except Exception:  # pragma: no cover - best-effort fallback
    rrf_fuse = None  # type: ignore
    _bm25_like = None  # type: ignore
    _dense_like = None  # type: ignore

from apps.api.aurora.db import init_db, get_session
from apps.api.aurora.retrieval import hybrid as _hybrid


# Ensure DB schema is present for tests that use TestClient against this shim
try:  # pragma: no cover
    init_db()
except Exception:
    pass


def hybrid_retrieval(q: str, top_n: int = 10, rerank_k: int = 6):
    # Prefer the private composition if all parts are present
    if callable(_bm25_like) and callable(_dense_like) and callable(rrf_fuse):  # type: ignore[arg-type]
        try:
            a = _bm25_like(q, top_n)  # type: ignore[misc]
            b = _dense_like(q, top_n)  # type: ignore[misc]
            return rrf_fuse([a, b], rerank_k)  # type: ignore[misc]
        except Exception:
            pass
    # Fallback to the public hybrid retrieval
    try:
        return _hybrid(q, top_n=top_n, rerank_k=rerank_k)
    except Exception:
        return []
