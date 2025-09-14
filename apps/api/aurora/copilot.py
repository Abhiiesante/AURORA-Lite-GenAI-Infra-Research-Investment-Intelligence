from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import time
from pydantic import BaseModel
from .db import get_session, Company, CopilotSession
from .rag_models import ComparativeAnswer, ComparisonRow
from sqlalchemy import text
def answer_with_citations(question: str) -> Dict[str, Any]:
    # Minimal stub so tests can monkeypatch this symbol without importing heavy deps.
    return {"answer": "Insufficient evidence", "sources": []}

try:
    from rapidfuzz import fuzz  # type: ignore

    def _sim(a: str, b: str) -> float:
        try:
            return float(fuzz.token_set_ratio(a, b))
        except Exception:
            return 0.0
except Exception:
    from difflib import SequenceMatcher

    def _sim(a: str, b: str) -> float:
        return 100.0 * SequenceMatcher(None, a, b).ratio()


class CopilotMemory(BaseModel):
    last_intent: Optional[str] = None
    selected_entities: List[int] = []
    window: Optional[str] = None
    citation_cache: List[str] = []


# Initialize in-memory cache globals to avoid 'possibly unbound' warnings
_DOC_CACHE: Dict[str, Tuple[float, List[str]]] = {}
_DOC_HITS: int = 0
_DOC_MISSES: int = 0


def _get_or_create_session(session_id: Optional[str]) -> Tuple[Optional[int], CopilotMemory]:
    if not session_id:
        return None, CopilotMemory()
    with get_session() as s:
        res = s.exec(
            """
            SELECT id, memory_json FROM copilot_sessions WHERE id = :sid
            """,
            params={"sid": int(session_id)} if str(session_id).isdigit() else {"sid": -1},
        )
        row = (list(res)[0] if res is not None and len(list(res)) > 0 else None)
        if row and isinstance(row, tuple):
            _, mem_json = row
            try:
                import json

                data = json.loads(mem_json or "{}")
                return int(session_id), CopilotMemory.model_validate(data)
            except Exception:
                return int(session_id), CopilotMemory()
    return None, CopilotMemory()


def _persist_memory(session_id: Optional[int], mem: CopilotMemory) -> None:
    if session_id is None:
        return
    try:
        import json
        with get_session() as s:
            # simple UPSERT via raw SQL to avoid ORM complexity here
            mem_json = json.dumps(mem.model_dump())
            s.exec(
                """
                INSERT INTO copilot_sessions(id, memory_json)
                VALUES (:sid, :mem)
                ON CONFLICT (id) DO UPDATE SET memory_json = EXCLUDED.memory_json
                """,
                params={"sid": session_id, "mem": mem_json},
            )
            s.commit()
    except Exception:
        # Best-effort only; swallow errors in free/local env
        pass


def _candidate_company_ids() -> List[Tuple[int, str]]:
    try:
        with get_session() as s:
            res = s.exec(text("SELECT id, canonical_name FROM companies LIMIT 200"))  # type: ignore[arg-type]
            rows = list(res) if res is not None else []
            out: List[Tuple[int, str]] = []
            for r in rows:
                try:
                    cid = int(r[0])
                    name = str(r[1])
                    out.append((cid, name))
                except Exception:
                    continue
            return out
    except Exception:
        return []


def detect_company_ids(question: str, top_k: int = 2) -> List[int]:
    # Optional spaCy NER
    ents: List[str] = []
    try:
        import spacy  # type: ignore
        try:
            nlp = spacy.load("en_core_web_sm")  # may fail if model missing
            doc = nlp(question)
            ents = [e.text for e in doc.ents if e.label_ in {"ORG", "PRODUCT", "PERSON"}]
        except Exception:
            pass
    except Exception:
        pass
    tokens = ents or question.split()
    cands = _candidate_company_ids()
    scored: List[Tuple[int, float]] = []
    for cid, name in cands:
        best = max((_sim(name, t) for t in tokens), default=0.0)
        if best >= 70:
            scored.append((cid, float(best)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [cid for cid, _ in scored[:top_k]]


def rrf_fuse(dense: List[str], sparse: List[str], k: int = 60, top_n: int = 10) -> List[str]:
    # Inputs are ranked URL lists; return fused top_n
    scores: Dict[str, float] = {}
    for i, u in enumerate(dense):
        scores[u] = scores.get(u, 0.0) + 1.0 / (k + i + 1)
    for i, u in enumerate(sparse):
        scores[u] = scores.get(u, 0.0) + 1.0 / (k + i + 1)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [u for u, _ in ranked[:top_n]]


def tool_company_lookup(name_or_id: str | int) -> Dict[str, Any]:
    with get_session() as s:
        if isinstance(name_or_id, int) or str(name_or_id).isdigit():
            c = s.get(Company, int(name_or_id))
        else:
            # naive lookup by canonical_name using text to satisfy typing
            res = s.exec(text("SELECT id, canonical_name, website, segments, hq_country FROM companies WHERE canonical_name = :n"), {"n": str(name_or_id)})  # type: ignore[arg-type]
            lst = list(res) if res is not None else []
            r = lst[0] if lst else None
            if r:
                class _C:  # minimal shim for struct-like access
                    id = r[0]
                    canonical_name = r[1]
                    website = r[2]
                    segments = r[3]
                    hq_country = r[4]
                c = _C()
            else:
                c = None
        if not c:
            return {}
        return {
            "id": c.id,
            "name": c.canonical_name,
            "website": c.website,
            "segments": c.segments,
            "hq_country": c.hq_country,
        }


def tool_compare_companies(ids: List[int], metrics: List[str]) -> List[ComparisonRow]:
    # TODO: pull aligned metrics; for now, return placeholders
    rows: List[ComparisonRow] = []
    for m in metrics[:5]:
        rows.append(ComparisonRow(metric=m, a="n/a", b="n/a", delta="n/a"))
    return rows


def tool_retrieve_docs(query: str, limit: int = 10) -> List[str]:
    # In-memory TTL cache to avoid repeated retrievals
    # key: query string -> (timestamp, urls)
    global _DOC_CACHE, _DOC_HITS, _DOC_MISSES  # type: ignore
    now = time.time()
    TTL = 600.0  # 10 minutes
    MAX_ENTRIES = 256
    cached = _DOC_CACHE.get(query)
    if cached:
        ts, urls_cached = cached
        if now - ts < TTL:
            _DOC_HITS += 1
            return list(urls_cached)[:limit]
    # Use existing hybrid retrieval + citations as fallback
    # Lazy import to avoid heavy deps at module import time; fall back to local stub
    try:
        from .rag_service import answer_with_citations as awc  # type: ignore
    except Exception:
        awc = answer_with_citations
    qa = awc(query)
    sources = [s.get("url") or s.get("source") for s in qa.get("sources", []) if s]
    # De-dup and trim
    seen = set()
    urls: List[str] = []
    for u in sources:
        if not u:
            continue
        if u in seen:
            continue
        seen.add(u)
        urls.append(u)
        if len(urls) >= limit:
            break
    # If RAG returned nothing, fall back to recent NewsItem/Filing URLs for detected companies
    if not urls:
        try:
            from sqlmodel import select  # type: ignore
            try:
                from .db import NewsItem, Filing  # type: ignore
            except Exception:
                NewsItem = None  # type: ignore
                Filing = None  # type: ignore
            ids = detect_company_ids(query, top_k=2)
            if ids and (NewsItem is not None or Filing is not None):
                with get_session() as s:  # type: ignore
                    for cid in ids:
                        try:
                            c = s.get(Company, cid)
                        except Exception:
                            c = None
                        canonical = getattr(c, "canonical_id", None) or getattr(c, "canonical_name", None) or str(cid)
                        if NewsItem is not None:
                            try:
                                qn = select(NewsItem).where(  # type: ignore
                                    getattr(NewsItem, "company_canonical_id") == canonical  # type: ignore
                                ).limit(10)
                                for ni in list(s.exec(qn) or []):  # type: ignore[attr-defined]
                                    u = getattr(ni, "url", None)
                                    if u and u not in seen:
                                        seen.add(u)
                                        urls.append(u)
                                        if len(urls) >= limit:
                                            return urls
                            except Exception:
                                pass
                        if Filing is not None:
                            try:
                                qf = select(Filing).where(  # type: ignore
                                    getattr(Filing, "company_canonical_id") == canonical  # type: ignore
                                ).limit(10)
                                for fi in list(s.exec(qf) or []):  # type: ignore[attr-defined]
                                    u = getattr(fi, "url", None)
                                    if u and u not in seen:
                                        seen.add(u)
                                        urls.append(u)
                                        if len(urls) >= limit:
                                            return urls
                            except Exception:
                                pass
        except Exception:
            pass
    # Store in cache
    try:
        _DOC_CACHE[query] = (now, list(urls))
        _DOC_MISSES += 1
        # simple size cap eviction: drop oldest entries beyond MAX_ENTRIES
        if len(_DOC_CACHE) > MAX_ENTRIES:
            try:
                oldest_key = min(_DOC_CACHE.items(), key=lambda kv: kv[1][0])[0]
                _DOC_CACHE.pop(oldest_key, None)
            except Exception:
                pass
    except Exception:
        pass
    return urls


def _clear_doc_cache() -> int:
    """Clear the in-memory document cache. Returns number of entries removed."""
    global _DOC_CACHE, _DOC_HITS, _DOC_MISSES  # type: ignore
    try:
        n = len(_DOC_CACHE)
        _DOC_CACHE.clear()
        _DOC_HITS = 0
        _DOC_MISSES = 0
        return n
    except Exception:
        return 0


def _get_doc_cache_stats() -> Dict[str, int]:
    global _DOC_CACHE, _DOC_HITS, _DOC_MISSES  # type: ignore
    try:
        size = len(_DOC_CACHE)
    except Exception:
        size = 0
    try:
        hits = int(_DOC_HITS)
    except Exception:
        hits = 0
    try:
        misses = int(_DOC_MISSES)
    except Exception:
        misses = 0
    return {"hits": hits, "misses": misses, "size": size}


def tool_trend_snapshot(segment: str | None, keyword: str | None, window: str = "90d") -> Dict[str, Any]:
    # TODO: implement real trend miner; placeholder deltas
    return {"window": window, "delta": 0.0}


def ask_copilot(session_id: Optional[str], question: str, context_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    sid, mem = _get_or_create_session(session_id)

    # Detect entities (companies) and limit to two
    ids: List[int] = detect_company_ids(question, top_k=2)
    metrics = ["signal_score", "stars_30d", "commits_30d"]

    rows = tool_compare_companies(ids[:2], metrics)
    sources = tool_retrieve_docs(question, limit=12)

    # Guardrail: citations must be non-empty
    if not sources:
        ans = ComparativeAnswer(answer="Insufficient evidence", comparisons=rows, top_risks=[], sources=[])
        return ans.model_dump()

    # Optionally persist minimal memory
    mem.last_intent = "compare" if ids else "ask"
    mem.selected_entities = ids
    _persist_memory(sid, mem)

    # Construct minimal answer without LLM to keep infra-free default
    answer_text = "Insufficient evidence"
    if ids:
        answer_text = "Preliminary comparison based on available sources."

    ans = ComparativeAnswer(answer=answer_text, comparisons=rows, top_risks=[], sources=sources)
    return ans.model_dump()
