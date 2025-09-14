from __future__ import annotations

"""
Prefect flow stubs for M2: metrics compute, signal score, and topic trends.
These are minimal, idempotent placeholders to be expanded later.
"""

from typing import Optional, List, Dict, Any, cast, Callable, TypeVar, overload
from .config import settings

try:
    from prefect import flow, task  # type: ignore
    _HAVE_PREFECT = True
except Exception:
    _HAVE_PREFECT = False


T = TypeVar("T", bound=Callable[..., Any])

@overload
def _noop_decorator(func: T) -> T: ...

@overload
def _noop_decorator(*, name: str = ...) -> Callable[[T], T]: ...

def _noop_decorator(*dargs, **dkwargs):
    """A flexible no-op decorator that supports both @decorator and @decorator(...).
    It ignores any decorator arguments and returns the original function unchanged.
    """
    if dargs and callable(dargs[0]) and len(dargs) == 1 and not dkwargs:
        func = dargs[0]
        return func
    def _inner(func: T) -> T:
        return func
    return _inner


# Only use real Prefect flows if explicitly enabled via settings to avoid
# heavy orchestration startup during tests. Otherwise use no-op decorators.
if _HAVE_PREFECT and getattr(settings, "use_prefect_flows", False):
    _flow = flow  # type: ignore[assignment]
    _task = task  # type: ignore[assignment]
else:
    _flow = _noop_decorator  # type: ignore[assignment]
    _task = _noop_decorator  # type: ignore[assignment]


@_task
def compute_company_metrics(company_id: Optional[int] = None, window: str = "90d") -> dict:
    # Placeholder: return deterministic structure
    return {"company_id": company_id, "window": window, "rows": 7}


@_task
def compute_signal_score(company_id: Optional[int] = None, week_start: Optional[str] = None) -> dict:
    return {"company_id": company_id, "week_start": week_start, "signal_score": 55.0}


@_task
def compute_topics(window: str = "90d") -> dict:
    # M4: BERTopic pipeline, gated by feature flag
    try:
        from .db import get_session, Topic, TopicTrend  # type: ignore
        from datetime import datetime, timedelta, timezone
        import json as _json
        # Lazy import helper to avoid hard import cycles at module import time
        try:
            from .trends import delta_and_change_flag as _delta_cf  # type: ignore
        except Exception:
            _delta_cf = None  # type: ignore

        # If topic modeling is enabled, try BERTopic fit/partial_fit
        if getattr(settings, "use_topic_modeling", False):
            try:
                from bertopic import BERTopic  # type: ignore
            except Exception:
                BERTopic = None

            # Load a simple corpus from news_items (titles) within window
            docs: List[str] = []
            try:
                # interpret window like "90d"
                days = 90
                try:
                    if window.endswith("d"):
                        days = int(window[:-1])
                except Exception:
                    days = 90
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                with get_session() as s:
                    rows = list(s.exec("SELECT title, published_at FROM news_items"))  # type: ignore[arg-type]
                    for r in rows:
                        title = r[0] if isinstance(r, (tuple, list)) else getattr(r, "title", None)
                        pub = r[1] if isinstance(r, (tuple, list)) else getattr(r, "published_at", None)
                        ok = True
                        try:
                            if pub:
                                dt = datetime.fromisoformat(str(pub))
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                                ok = dt >= cutoff
                        except Exception:
                            ok = True
                        if title and ok:
                            docs.append(str(title))
            except Exception:
                pass
            if not docs:
                docs = [
                    "Vector DBs gain traction in GenAI infra.",
                    "Embedding models improve semantic search.",
                    "Open-source frameworks for retrieval augmented generation.",
                ]
            topic_model = None
            topics, probs = [], []
            examples, terms = [], []

            # Periodic refit gate: only refit if last updated older than topic_refit_days
            should_refit = True
            try:
                days = int(getattr(settings, "topic_refit_days", 7))
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                with get_session() as s:
                    rows = []
                    try:
                        rows = list(s.exec("SELECT updated_at FROM topics ORDER BY updated_at DESC LIMIT 1"))  # type: ignore[arg-type]
                    except Exception:
                        rows = []
                    if rows:
                        latest = rows[0][0] if isinstance(rows[0], (tuple, list)) else getattr(rows[0], "updated_at", None)
                        if latest:
                            try:
                                dt = datetime.fromisoformat(str(latest))
                                should_refit = dt < cutoff
                            except Exception:
                                should_refit = True
            except Exception:
                should_refit = True

            if BERTopic:
                try:
                    if should_refit:
                        topic_model = BERTopic()
                        topics, probs = topic_model.fit_transform(docs)
                    # Extract top terms and examples for topic 0
                    if topic_model and hasattr(topic_model, "get_topic"):
                        terms = topic_model.get_topic(0)
                    examples = [docs[i] for i, t in enumerate(topics) if t == 0] if topics else []
                except Exception:
                    topics, probs, examples, terms = [], [], [], []

            # Persist topic and trends
            with get_session() as s:
                label = "GenAI Infra"
                nowiso = datetime.now(timezone.utc).isoformat()
                t = Topic(label=label, terms_json=_json.dumps([w[0] for w in terms[:5]] if terms else ["vector", "embedding"]), examples_json=_json.dumps(examples), updated_at=nowiso)  # type: ignore[call-arg]
                try:
                    s.add(t)  # type: ignore[attr-defined]
                except Exception:
                    pass
                today = datetime.now(timezone.utc).date()
                weeks: List[str] = [(today - timedelta(days=i*7)).isoformat() for i in range(2, -1, -1)]
                # Derive simple weekly frequencies from doc count trend (placeholder)
                base = max(1, len(docs) // 3)
                freqs = [float(base), float(base*1.1), float(base*1.3)]
                helper_flag = False
                if _delta_cf is not None:
                    d, f = _delta_cf(freqs)
                    helper_flag = bool(f)
                # Optional ruptures change-point
                try:
                    import ruptures as rpt  # type: ignore
                    import numpy as np  # type: ignore
                    arr = np.array(freqs).reshape(-1, 1)
                    model = rpt.Binseg(model='l2').fit(arr)
                    _ = model.predict(n_bkps=1)
                    helper_flag = True if len(freqs) >= 3 and (freqs[-1] - freqs[-2]) > (freqs[-2] - freqs[-3]) else helper_flag
                except Exception:
                    pass
                created = 0
                for i, ws in enumerate(weeks):
                    try:
                        row = TopicTrend(  # type: ignore[call-arg]
                            topic_id=int(getattr(t, "topic_id", 1) or 1),
                            week_start=ws,
                            freq=freqs[i],
                            delta=(freqs[i] - freqs[i-1]) if i > 0 else 0.0,
                            change_flag=(i == len(weeks) - 1 and helper_flag),
                        )
                        s.add(row)  # type: ignore[attr-defined]
                        created += 1
                    except Exception:
                        continue
                try:
                    s.commit()  # type: ignore[attr-defined]
                except Exception:
                    pass
            return {"window": window, "topics": 1, "trend_rows": created, "topic_modeling": True}

        # Fallback: demo topic/trend as before
        with get_session() as s:  # type: ignore
            label = "GenAI Infra"
            nowiso = datetime.now(timezone.utc).isoformat()
            t = Topic(label=label, terms_json=_json.dumps(["vector", "embedding"]), updated_at=nowiso)  # type: ignore[call-arg]
            try:
                s.add(t)  # type: ignore[attr-defined]
            except Exception:
                pass
            today = datetime.now(timezone.utc).date()
            weeks: List[str] = [(today - timedelta(days=i*7)).isoformat() for i in range(2, -1, -1)]
            freqs = [1.0, 1.2, 1.6]
            helper_flag = False
            if _delta_cf is not None:
                d, f = _delta_cf(freqs)
                helper_flag = bool(f)
            created = 0
            for i, ws in enumerate(weeks):
                try:
                    row = TopicTrend(  # type: ignore[call-arg]
                        topic_id=int(getattr(t, "topic_id", 1) or 1),
                        week_start=ws,
                        freq=freqs[i],
                        delta=(freqs[i] - freqs[i-1]) if i > 0 else 0.0,
                        change_flag=(i == len(weeks) - 1 and helper_flag),
                    )
                    s.add(row)  # type: ignore[attr-defined]
                    created += 1
                except Exception:
                    continue
            try:
                s.commit()  # type: ignore[attr-defined]
            except Exception:
                pass
        return {"window": window, "topics": 1, "trend_rows": created, "topic_modeling": False}
    except Exception:
        return {"window": window, "topics": 1}


# --- M4: Topic modeling & change-points (scaffold) ---
@_task
def build_weekly_corpus(window: str = "90d") -> dict:
    # Placeholder: return doc counts
    return {"window": window, "docs": 100}


@_task
def train_bertopic(initial_months: int = 1) -> dict:
    # Placeholder for BERTopic fit
    return {"status": "trained", "months": initial_months}


@_task
def detect_changepoints(topic_id: int, window: str = "90d") -> dict:
    # Placeholder for ruptures
    return {"topic_id": topic_id, "window": window, "changes": 0}


# --- M8: Ingestion & quality gates (scaffold) ---
@_task
def ingest_feeds(batch: int = 50) -> dict:
    return {"ingested": batch}


@_task
def deduplicate_items() -> dict:
    return {"deduped": True}


@_task
def validate_quality() -> dict:
    return {"passed": True}


@_flow(name="m2-refresh-company")
def refresh_company(company_id: int, window: str = "90d") -> dict:
    # When using no-op decorators, tasks return dicts directly; under Prefect they return futures.
    metrics = cast(Any, compute_company_metrics)(company_id=company_id, window=window)
    score = cast(Any, compute_signal_score)(company_id=company_id)
    return {"metrics": metrics, "score": score}


@_flow(name="m2-refresh-topics")
def refresh_topics(window: str = "90d") -> dict:
    corpus = build_weekly_corpus(window)
    _ = train_bertopic(1)
    t = compute_topics(window)
    # would call detect_changepoints per topic
    return {"corpus": corpus, "topics": t}
