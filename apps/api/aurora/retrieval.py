from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .config import settings

_embedder = None
_reranker = None


def _load_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        _embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        return _embedder
    except Exception:
        return None


def _load_reranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    if not getattr(settings, "rerank_enabled", True):
        return None
    try:
        from sentence_transformers import CrossEncoder  # type: ignore

        _reranker = CrossEncoder("BAAI/bge-reranker-base")
        return _reranker
    except Exception:
        return None


def _qdrant_search(query: str, limit: int = 12) -> List[Dict[str, Any]]:
    # Lazy import to avoid heavy dependency at module import time
    try:
        from .clients import qdrant  # type: ignore
    except Exception:
        qdrant = None  # type: ignore
    if not qdrant:
        return []
    emb = None
    emb_model = _load_embedder()
    if emb_model:
        try:
            vec = emb_model.encode(query)
            emb = vec.tolist() if hasattr(vec, "tolist") else list(vec)
        except Exception:
            emb = None
    if not emb:
        return []
    try:
        res = qdrant.search(collection_name="documents", query_vector=emb, limit=limit)
        out: List[Dict[str, Any]] = []
        for p in res:
            payload = getattr(p, "payload", {}) or {}
            out.append(
                {
                    "id": str(getattr(p, "id", payload.get("id") or payload.get("doc_id") or "")),
                    "url": payload.get("url") or "",
                    "text": payload.get("text") or "",
                    "tags": payload.get("tags") or [],
                    "_score": float(getattr(p, "score", 0.0) or 0.0),
                }
            )
        return out
    except Exception:
        return []


def _meili_search(query: str, limit: int = 12) -> List[Dict[str, Any]]:
    # Lazy import to avoid heavy dependency at module import time
    try:
        from .clients import meili  # type: ignore
    except Exception:
        meili = None  # type: ignore
    if not meili:
        return []
    try:
        idx = meili.index("documents")
        res = idx.search(query, {"limit": limit})
        out: List[Dict[str, Any]] = []
        for h in res.get("hits", []) or []:
            out.append(
                {
                    "id": str(h.get("id") or h.get("_id") or h.get("url") or h.get("doc_id") or ""),
                    "url": h.get("url") or "",
                    "text": h.get("text") or "",
                    "tags": h.get("tags") or [],
                }
            )
        return out
    except Exception:
        return []


def _token_rerank(query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    q_tokens = set(query.lower().split())
    scored = []
    for d in docs:
        text = (d.get("text") or "") + " " + " ".join(d.get("tags") or [])
        s = sum(2 for t in q_tokens if t in text.lower())
        scored.append((s, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:top_k]]


def _bge_rerank(query: str, docs: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    rr = _load_reranker()
    if not rr or not docs:
        return _token_rerank(query, docs, top_k)
    try:
        pairs = [(query, d.get("text") or "") for d in docs]
        scores = rr.predict(pairs)  # type: ignore
        ranked = list(zip(scores, docs))
        ranked.sort(key=lambda x: float(x[0]), reverse=True)
        return [d for _, d in ranked[:top_k]]
    except Exception:
        return _token_rerank(query, docs, top_k)


def rrf_fuse(rank_lists: List[List[Dict[str, Any]]], k: int = 60) -> List[Dict[str, Any]]:
    rank_maps = []
    for lst in rank_lists:
        rank = {str(doc.get("id")): i + 1 for i, doc in enumerate(lst)}
        rank_maps.append(rank)
    scores: Dict[str, float] = {}
    for ranks in rank_maps:
        for doc_id, r in ranks.items():
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + r)
    # flatten and build id->doc mapping by first occurrence priority
    flat: List[Dict[str, Any]] = [d for lst in rank_lists for d in lst]
    id_to_doc: Dict[str, Dict[str, Any]] = {}
    for d in flat:
        did = str(d.get("id"))
        if did and did not in id_to_doc:
            id_to_doc[did] = d
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [id_to_doc[i] for i, _ in fused if i in id_to_doc]


def hybrid(query: str, top_n: int = 10, rerank_k: int = 6) -> List[Dict[str, Any]]:
    dense = _qdrant_search(query, limit=12)
    sparse = _meili_search(query, limit=12)
    if not dense and not sparse:
        return []
    fused = rrf_fuse([dense, sparse])[:top_n]
    reranked = _bge_rerank(query, fused, top_k=rerank_k)
    return reranked


def validate_citations(citations: List[Any], retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate and normalize citations against retrieved documents.
    - citations may be list of URLs or objects with 'url'
    - retrieved_docs contain 'url' fields; only those are allowed
    Returns a report with: valid_urls, invalid_urls, suggested_urls (fallback to first retrieved if empty).
    """
    allow = {d.get("url") for d in retrieved_docs if d.get("url")}
    raw_urls: List[str] = []
    for c in citations or []:
        if isinstance(c, str):
            raw_urls.append(c)
        elif isinstance(c, dict) and c.get("url"):
            raw_urls.append(c.get("url"))
    valid = [u for u in raw_urls if u in allow]
    invalid = [u for u in raw_urls if u not in allow]
    suggested: List[str] = []
    if not valid and retrieved_docs:
        u = retrieved_docs[0].get("url")
        if u:
            suggested = [u]
    return {
        "valid_urls": valid,
        "invalid_urls": invalid,
        "suggested_urls": suggested,
    }
