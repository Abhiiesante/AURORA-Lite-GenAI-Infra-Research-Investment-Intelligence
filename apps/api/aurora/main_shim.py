# Shim so tests importing `aurora.main` resolve to the app
from apps.api.aurora.main import app, settings, _DOCS, _rrf_fuse as rrf_fuse, _bm25_like, _dense_like, _ensure_citations
from apps.api.aurora.db import init_db, get_session


def hybrid_retrieval(q: str, top_n: int = 10, rerank_k: int = 6):
    a = _bm25_like(q, top_n)
    b = _dense_like(q, top_n)
    return rrf_fuse(a, b)
