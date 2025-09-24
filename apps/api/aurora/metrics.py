from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Sequence, Any
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .db import get_session, CompanyMetric
try:
    from .db import SignalSnapshot, Alert  # type: ignore
    _HAVE_SIGNAL_MODELS = True
except Exception:
    SignalSnapshot = None  # type: ignore
    Alert = None  # type: ignore
    _HAVE_SIGNAL_MODELS = False
from .config import settings


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            return float(x)
        # strings and other types
        return float(str(x))
    except Exception:
        return default

# Optional DuckDB import (local compute)
try:
    import duckdb  # type: ignore
    _HAVE_DUCKDB = True
except Exception:
    _HAVE_DUCKDB = False


def _week_series(n: int = 7) -> List[str]:
    today = datetime.now(timezone.utc).date()
    days = [today - timedelta(days=i) for i in range(n - 1, -1, -1)]
    return [d.isoformat() for d in days]


def _segment_stats(metric: str, company_id: int) -> Optional[Tuple[float, float]]:
    """Approximate segment-wise stats (mean,std) for a metric across companies in the same segment.
    Falls back to None if not available. Uses all-time values; lightweight approximation.
    """
    try:
        from sqlmodel import select  # type: ignore
        from .db import Company  # type: ignore
        with get_session() as s:  # type: ignore
            # Get target company's segments
            c = s.get(Company, int(company_id))
            segs = set((getattr(c, "segments", "") or "").split(",")) if c else set()
            if not segs:
                return None
            # Find other companies sharing any segment
            comp_rows = list(s.exec(select(Company)).all())  # type: ignore[attr-defined]
            cohort_ids = [int(getattr(r, "id", 0) or 0) for r in comp_rows if r and segs.intersection(set((getattr(r, "segments", "") or "").split(",")))]
            if not cohort_ids:
                return None
            # Gather metric values across cohort
            vals: List[float] = []
            for cid in cohort_ids:
                rows = list(s.exec(select(CompanyMetric).where(CompanyMetric.company_id == cid)).all())  # type: ignore[attr-defined]
                for row in rows:
                    v = getattr(row, metric, None)
                    if v is not None:
                        try:
                            vals.append(float(v))
                        except Exception:
                            continue
            if len(vals) < 3:
                return None
            mean = sum(vals) / len(vals)
            var = sum((x - mean) ** 2 for x in vals) / max(1, len(vals) - 1)
            std = var ** 0.5 if var > 0 else 1.0
            return (mean, std)
    except Exception:
        return None


def _fetch_cached_metrics(company_id: int, window: str) -> List[CompanyMetric]:
    try:
        # Attempt a typed query if SQLModel is available
        from sqlmodel import select  # type: ignore

        with get_session() as s:  # type: ignore
            try:
                stmt = select(CompanyMetric).where(CompanyMetric.company_id == company_id)  # type: ignore
                result = s.exec(stmt)  # type: ignore[attr-defined]
                rows = list(result)
                return rows
            except Exception:
                # Fallback: no exec/select support
                return []
    except Exception:
        return []


def _resolve_parquet_dir() -> Optional[str]:
    """Resolve a parquet directory from settings or default to data/marts.
    Returns a string path or None if not resolvable.
    """
    if getattr(settings, "parquet_dir", None):  # type: ignore[attr-defined]
        return settings.parquet_dir  # type: ignore[return-value]
    # Default to repo-relative data/marts
    try:
        here = Path(__file__).resolve()
        repo_root = here.parents[3]  # apps/api/aurora/... -> repo root
        default_dir = repo_root / "data" / "marts"
        if default_dir.exists():
            return str(default_dir)
    except Exception:
        pass
    return None


def _compute_metrics_duckdb(company_id: int, window: str) -> Dict[str, float]:
    if not _HAVE_DUCKDB:
        return {}
    base = _resolve_parquet_dir()
    if not base:
        return {}
    # Attempt to scan a conventional path if exists; otherwise return empty
    try:
        # Example expected layout: <parquet_dir>/company_metrics/*.parquet with columns:
        # company_id, week_start, mentions, filings, stars, commits, sentiment, signal_score
        metrics_glob = Path(base) / "company_metrics" / "*.parquet"
        if not any(Path(base).glob("company_metrics/*.parquet")):
            return {}
        # Load duckdb lazily to satisfy type checkers
        import importlib as _importlib
        duck = _importlib.import_module("duckdb")
        con = duck.connect()
        # Precompute posix path to avoid backslash in f-string expression (Py 3.11 restriction)
        _parquet_path = metrics_glob.as_posix()
        tbl = f"read_parquet('{_parquet_path}')"
        # Get latest snapshot for this company
        q = f"""
        SELECT * FROM {tbl}
        WHERE company_id = {company_id}
        ORDER BY week_start DESC
        LIMIT 1
        """
        df = con.execute(q).fetchdf()
        if df is None or df.empty:
            return {}
        row = df.iloc[0]
        return {
            "mentions_7d": float(row.get("mentions", 0) or 0),
            "filings_90d": float(row.get("filings", 0) or 0),
            "stars_30d": float(row.get("stars", 0) or 0),
            "commits_30d": float(row.get("commits", 0) or 0),
            "sentiment_30d": float(row.get("sentiment", 0.0) or 0.0),
            "signal_score": _safe_float(row.get("signal_score", 0.0), 0.0),
        }
    except Exception:
        return {}


def _load_mentions_series_duckdb(company_id: int, take: int = 7) -> List[Dict[str, object]]:
    """Load up to 'take' points of mentions time series using DuckDB parquet.
    Returns a list of {date, value} dicts ordered ascending by date.
    """
    if not _HAVE_DUCKDB:
        return []
    base = _resolve_parquet_dir()
    if not base:
        return []
    try:
        metrics_glob = Path(base) / "company_metrics" / "*.parquet"
        if not any(Path(base).glob("company_metrics/*.parquet")):
            return []
        import importlib as _importlib
        duck = _importlib.import_module("duckdb")
        con = duck.connect()
        _parquet_path = metrics_glob.as_posix()
        tbl = f"read_parquet('{_parquet_path}')"
        q = f"""
        SELECT week_start, mentions
        FROM {tbl}
        WHERE company_id = {company_id}
        ORDER BY week_start ASC
        """
        df = con.execute(q).fetchdf()
        if df is None or df.empty:
            return []
        sub = df.iloc[-min(take, len(df)) :]
        out: List[Dict[str, object]] = []
        for _, row in sub.iterrows():
            dt = str(row["week_start"]) if "week_start" in row else ""
            v = row["mentions"] if (hasattr(row, "__getitem__") and "mentions" in row) else (row.get("mentions", 0) if hasattr(row, "get") else 0)
            try:
                val = float(v or 0)
            except Exception:
                val = 0.0
            out.append({"date": dt, "value": val})
        return out
    except Exception:
        return []


def _compute_dashboard_duckdb(company_id: int, window: str) -> Tuple[Dict[str, float], List[Dict[str, object]], List[str]]:
    """Compute KPIs and simple sparklines from DuckDB parquet if available.
    Returns (kpis, sparklines, sources). Falls back to empty on any failure.
    """
    if not _HAVE_DUCKDB:
        return {}, [], []
    base = _resolve_parquet_dir()
    if not base:
        return {}, [], []
    try:
        metrics_glob = Path(base) / "company_metrics" / "*.parquet"
        if not any(Path(base).glob("company_metrics/*.parquet")):
            return {}, [], []
        import importlib as _importlib
        duck = _importlib.import_module("duckdb")
        con = duck.connect()
        _parquet_path = metrics_glob.as_posix()
        tbl = f"read_parquet('{_parquet_path}')"
        # Filter by company and order ascending by week_start
        q = f"""
        SELECT week_start, mentions, filings, stars, commits, sentiment, signal_score
        FROM {tbl}
        WHERE company_id = {company_id}
        ORDER BY week_start ASC
        """
        df = con.execute(q).fetchdf()
        if df is None or df.empty:
            return {}, [], []
        # KPIs from the last row
        last = df.iloc[-1]
        kpis = {
            "mentions_7d": float(last.get("mentions", 0) or 0),
            "filings_90d": float(last.get("filings", 0) or 0),
            "stars_30d": float(last.get("stars", 0) or 0),
            "commits_30d": float(last.get("commits", 0) or 0),
            "sentiment_30d": float(last.get("sentiment", 0.0) or 0.0),
            "signal_score": float(last.get("signal_score", 0.0) or 0.0),
        }
        # Optional sources column (either JSON string or array-like)
        srcs: List[str] = []
        # Optional metric-specific sources (mentions/stars/commits/sentiment)
        src_mentions: List[str] = []
        src_stars: List[str] = []
        src_commits: List[str] = []
        src_sent: List[str] = []
        try:
            if "sources" in df.columns or "source_urls" in df.columns:
                raw = last.get("sources") if "sources" in df.columns else last.get("source_urls")
                if raw is not None:
                    if isinstance(raw, list):
                        srcs = [str(u) for u in raw if u]
                    elif isinstance(raw, str):
                        # try JSON first, otherwise split by comma
                        try:
                            import json as _json
                            parsed = _json.loads(raw)
                            if isinstance(parsed, list):
                                srcs = [str(u) for u in parsed if u]
                            else:
                                srcs = [s.strip() for s in raw.split(",") if s.strip()]
                        except Exception:
                            srcs = [s.strip() for s in raw.split(",") if s.strip()]
            # Metric-specific sources: columns like mentions_sources, stars_sources, commits_sources, sentiment_sources
            def _parse_src(col: str) -> List[str]:
                if col in df.columns:
                    val = last.get(col)
                    if isinstance(val, list):
                        return [str(u) for u in val if u]
                    if isinstance(val, str):
                        try:
                            import json as _json
                            parsed = _json.loads(val)
                            if isinstance(parsed, list):
                                return [str(u) for u in parsed if u]
                        except Exception:
                            pass
                        return [s.strip() for s in val.split(",") if s.strip()]
                return []
            src_mentions = _parse_src("mentions_sources") or _parse_src("mentions_source_urls")
            src_stars = _parse_src("stars_sources") or _parse_src("stars_source_urls")
            src_commits = _parse_src("commits_sources") or _parse_src("commits_source_urls")
            src_sent = _parse_src("sentiment_sources") or _parse_src("sentiment_source_urls")
        except Exception:
            srcs, src_mentions, src_stars, src_commits, src_sent = [], [], [], [], []
        # Build sparklines (last 7) for mentions, stars, commits
        take = min(7, len(df))
        sub = df.iloc[-take:]
        def _series(col: str) -> List[Dict[str, object]]:
            out: List[Dict[str, object]] = []
            for _, row in sub.iterrows():
                dt = str(row["week_start"]) if "week_start" in row else ""
                vraw = row[col] if (hasattr(row, "__getitem__") and col in row) else (row.get(col, 0) if hasattr(row, "get") else 0)
                try:
                    v = float(vraw or 0)
                except Exception:
                    v = 0.0
                out.append({"date": dt, "value": v})
            return out
        series_mentions = _series("mentions")
        series_stars = _series("stars")
        series_commits = _series("commits")
        sparklines = [
            {"metric": "mentions_7d", "series": series_mentions, "sources": (src_mentions or srcs)},
            {"metric": "stars_30d", "series": series_stars, "sources": (src_stars or srcs)},
            {"metric": "commits_30d", "series": series_commits, "sources": (src_commits or srcs)},
        ]
        return kpis, sparklines, srcs
    except Exception:
        return {}, [], []


def get_dashboard(company_id: int, window: str = "90d") -> Tuple[Dict[str, float], List[Dict[str, object]], List[str]]:
    # Try cache first
    cached = _fetch_cached_metrics(company_id, window)
    kpis: Dict[str, float] = {}
    sparklines: List[Dict[str, object]] = []
    sources: List[str] = []
    if cached:
        # Use the last snapshot's fields as KPIs
        last = cached[-1]
        for key in ("mentions", "filings", "stars", "commits"):
            val = getattr(last, key, None)
            if val is not None:
                # map to expected KPI names
                if key == "mentions":
                    kpis["mentions_7d"] = float(val)
                elif key == "filings":
                    kpis["filings_90d"] = float(val)
                elif key == "stars":
                    kpis["stars_30d"] = float(val)
                elif key == "commits":
                    kpis["commits_30d"] = float(val)
        # optional fields
        if getattr(last, "sentiment", None) is not None:
            kpis["sentiment_30d"] = float(getattr(last, "sentiment"))
        if getattr(last, "signal_score", None) is not None:
            kpis["signal_score"] = float(getattr(last, "signal_score"))
        # Phase-3 optional KPIs
        if getattr(last, "hiring", None) is not None:
            try:
                kpis["hiring_30d"] = float(getattr(last, "hiring"))
            except Exception:
                pass
        if getattr(last, "patents", None) is not None:
            try:
                kpis["patents_90d"] = float(getattr(last, "patents"))
            except Exception:
                pass
        # Build sparkline series from cached rows (mentions over up to 7 points)
        try:
            rows_sorted = sorted(cached, key=lambda r: getattr(r, "week_start", ""))
        except Exception:
            rows_sorted = cached
        last_rows = rows_sorted[-7:]
        dates = [getattr(r, "week_start", "") or d for r, d in zip(last_rows, _week_series(len(last_rows)))]
        def _s(col: str) -> List[Dict[str, object]]:
            seq: List[Dict[str, object]] = []
            for r, dt in zip(last_rows, dates):
                try:
                    seq.append({"date": dt, "value": float(getattr(r, col, 0) or 0)})
                except Exception:
                    seq.append({"date": dt, "value": 0.0})
            return seq
        series_mentions = _s("mentions")
        series_stars = _s("stars")
        series_commits = _s("commits")
        series_sentiment = [
            {"date": dt, "value": float(getattr(r, "sentiment", 0.0) or 0.0)}
            for r, dt in zip(last_rows, dates)
        ]
        series_hiring = [
            {"date": dt, "value": float(getattr(r, "hiring", 0.0) or 0.0)}
            for r, dt in zip(last_rows, dates)
        ]
        series_patents = [
            {"date": dt, "value": float(getattr(r, "patents", 0.0) or 0.0)}
            for r, dt in zip(last_rows, dates)
        ]
        sparklines = [
            {"metric": "mentions_7d", "series": series_mentions, "sources": []},
            {"metric": "stars_30d", "series": series_stars, "sources": []},
            {"metric": "commits_30d", "series": series_commits, "sources": []},
        ]
        # Only include sentiment sparkline if any non-zero values to avoid noise
        if any(p.get("value", 0) for p in series_sentiment):
            sparklines.append({"metric": "sentiment_30d", "series": series_sentiment, "sources": []})
        # Optional: include hiring/patents sparklines if present and non-zero
        if any(p.get("value", 0) for p in series_hiring):
            sparklines.append({"metric": "hiring_30d", "series": series_hiring, "sources": []})
        if any(p.get("value", 0) for p in series_patents):
            sparklines.append({"metric": "patents_90d", "series": series_patents, "sources": []})
        # Optionally enrich with company-level KPIs like funding_total
        try:
            from .db import Company  # type: ignore
            with get_session() as s:  # type: ignore
                c = s.get(Company, int(company_id))
            if c and getattr(c, "funding_total", None) is not None:
                kpis["funding_total"] = float(getattr(c, "funding_total"))
        except Exception:
            pass
    else:
        # Try computing via DuckDB for richer output (optional)
        dk_kpis, dk_sparks, dk_sources = _compute_dashboard_duckdb(company_id, window)
        if dk_kpis:
            kpis.update(dk_kpis)
            sparklines = dk_sparks
            sources = dk_sources
        else:
            # Fallback: compute single-row KPIs via DuckDB (older helper)
            comp = _compute_metrics_duckdb(company_id, window)
            if comp:
                kpis.update(comp)

    # If we still have no sparklines, build simple placeholder series
    if not sparklines:
        days = _week_series(7)
        sparklines = [
            {"metric": "mentions_7d", "series": [{"date": d, "value": i * 3 + 1} for i, d in enumerate(days)], "sources": []},
        ]

    # Ensure minimum KPIs exist with placeholders
    defaults: Dict[str, float] = {
        "mentions_7d": 12.0,
        "filings_90d": 1.0,
        "stars_30d": 42.0,
        "commits_30d": 15.0,
        "sentiment_30d": 0.1,
        "signal_score": 55.0,
        # M6 extras
        "funding_total": 0.0,
        "rounds_count": 0.0,
    }
    for k, v in defaults.items():
        kpis.setdefault(k, v)

    return kpis, sparklines, sources


def _persist_signal_series(company_id: int, series: List[Dict[str, object]]) -> None:
    if not _HAVE_SIGNAL_MODELS or not series:
        return
    try:
        # Best-effort insert last few points to avoid unbounded writes
        with get_session() as s:  # type: ignore
            for pt in series[-3:]:
                try:
                    snap = SignalSnapshot(  # type: ignore[call-arg]
                        company_id=company_id,
                        week_start=str(pt.get("date", "")),
                        signal_score=_safe_float(pt.get("signal_score", 0.0), 0.0),
                        components_json=(
                            __import__("json").dumps(pt.get("components")) if pt.get("components") else None
                        ),
                    )
                    s.add(snap)  # type: ignore[attr-defined]
                except Exception:
                    continue
            try:
                s.commit()  # type: ignore[attr-defined]
            except Exception:
                pass
    except Exception:
        # swallow persistence errors silently
        pass


def _persist_alerts(company_id: int, alerts: List[Dict[str, object]]) -> None:
    if not _HAVE_SIGNAL_MODELS or not alerts:
        return
    try:
        with get_session() as s:  # type: ignore
            for a in alerts[-5:]:  # cap writes
                try:
                    urls = a.get("evidence_urls") or []
                    if isinstance(urls, list):
                        import json as _json
                        urls_json = _json.dumps(urls)
                    else:
                        urls_json = "[]"
                    sd_raw = a.get("score_delta", 0.0)
                    sd_val = _safe_float(sd_raw, 0.0)
                    row = Alert(  # type: ignore[call-arg]
                        company_id=company_id,
                        type=str(a.get("type", "threshold_crossing")),
                        score_delta=sd_val,
                        reason=str(a.get("reason")) if a.get("reason") is not None else None,
                        evidence_urls=urls_json,
                        created_at=str(a.get("date", "")),
                    )
                    s.add(row)  # type: ignore[attr-defined]
                    # Best-effort audit trail
                    try:
                        from .db import AuditEvent  # type: ignore
                        meta = {
                            "company_id": company_id,
                            "type": a.get("type"),
                            "reason": a.get("reason"),
                            "score_delta": a.get("score_delta"),
                            "confidence": a.get("confidence"),
                            "trace_id": a.get("trace_id"),
                        }
                        evt = AuditEvent(  # type: ignore[call-arg]
                            ts=str(a.get("date", "")),
                            actor="system",
                            role="service/compute",
                            action="alert.created",
                            resource=f"company:{company_id}",
                            meta_json=(__import__("json").dumps(meta)),
                        )
                        s.add(evt)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                except Exception:
                    continue
            try:
                s.commit()  # type: ignore[attr-defined]
            except Exception:
                pass
    except Exception:
        pass


def _load_signal_config() -> tuple[dict, float, float]:
    """Load (weights, alpha, delta_threshold) from DB if available; else defaults/settings.
    Returns (weights_dict, alpha, delta_threshold).
    """
    weights = {
        "mentions_7d": 0.35,
        "commit_velocity_30d": 0.25,
        "stars_growth_30d": 0.15,
        "filings_90d": 0.15,
        "sentiment_30d": 0.10,
    }
    alpha = 0.4
    delta_thr = float(getattr(settings, "alert_delta_threshold", 5.0))
    try:
        from sqlmodel import select  # type: ignore
        from .db import SignalConfigRow  # type: ignore
        with get_session() as s:  # type: ignore
            rows = list(s.exec(select(SignalConfigRow).order_by(SignalConfigRow.updated_at.desc()).limit(1)))  # type: ignore[attr-defined]
            if rows:
                r = rows[0]
                import json as _json
                wj = getattr(r, "weights_json", None)
                if wj:
                    parsed = _json.loads(wj)
                    if isinstance(parsed, dict):
                        weights.update({k: float(v) for k, v in parsed.items() if isinstance(v, (int, float))})
                if getattr(r, "alpha", None) is not None:
                    alpha = float(getattr(r, "alpha"))
                if getattr(r, "delta_threshold", None) is not None:
                    delta_thr = float(getattr(r, "delta_threshold"))
    except Exception:
        pass
    return weights, alpha, delta_thr


def compute_signal_series(company_id: int, window: str = "90d") -> List[Dict[str, object]]:
    """Compute composite signal score S per week with EMA smoothing.
    S = 0.35*z(mentions_7d) + 0.25*z(commit_velocity_30d) + 0.15*z(stars_growth_30d)
        + 0.15*z(filings_90d) + 0.10*z(sentiment_30d)
    - Segment-wise z-scores: approximation via local-window z on each series for this company
    - Clamp z to [-3, +3]; EMA(alpha=0.4) over S; scale to [0,100] via 50 + 25*S_z
    """
    rows = _fetch_cached_metrics(company_id, window)

    def _z(seq: Sequence[float], cohort: Optional[Tuple[float, float]] = None) -> List[float]:
        if not seq:
            return []
        if cohort is not None:
            mean, std = cohort
            std = std or 1.0
        else:
            mean = sum(seq) / len(seq)
            var = sum((x - mean) ** 2 for x in seq) / max(1, len(seq) - 1)
            std = var ** 0.5 if var > 0 else 1.0
        zs = [max(-3.0, min(3.0, (x - mean) / std)) for x in seq]
        return zs

    weights_cfg, alpha_cfg, _ = _load_signal_config()

    def _ema(seq: Sequence[float], alpha: float = alpha_cfg) -> List[float]:
        if not seq:
            return []
        out = []
        prev = seq[0]
        for x in seq:
            prev = alpha * x + (1 - alpha) * prev
            out.append(prev)
        return out

    # Build aligned weekly vectors
    if rows:
        try:
            rows_sorted = sorted(rows, key=lambda r: getattr(r, "week_start", ""))
        except Exception:
            rows_sorted = rows
        dates = [getattr(r, "week_start", "") or d for r, d in zip(rows_sorted, _week_series(len(rows_sorted)))]
        mentions = [float(getattr(r, "mentions", 0) or 0) for r in rows_sorted]
        filings = [float(getattr(r, "filings", 0) or 0) for r in rows_sorted]
        stars = [float(getattr(r, "stars", 0) or 0) for r in rows_sorted]
        commits = [float(getattr(r, "commits", 0) or 0) for r in rows_sorted]
        sentiment = [float(getattr(r, "sentiment", 0.0) or 0.0) for r in rows_sorted]
        hiring = [float(getattr(r, "hiring", 0) or 0) for r in rows_sorted]
        patents = [float(getattr(r, "patents", 0) or 0) for r in rows_sorted]
    else:
        # fallback synthetic vectors if no cache; try DuckDB mentions series as base for dates
        pts = _load_mentions_series_duckdb(company_id, take=7)
        if pts:
            dates = [str(p.get("date", "")) for p in pts]
            mentions = [_safe_float(p.get("value", 0.0), 0.0) for p in pts]
        else:
            dates = _week_series(7)
            mentions = [10, 12, 11, 13, 14, 15, 16]
        filings = [1 for _ in dates]
        stars = [42 for _ in dates]
        commits = [15 for _ in dates]
        sentiment = [0.1 for _ in dates]
        hiring = [0.0 for _ in dates]
        patents = [0.0 for _ in dates]

    # Derived components
    # commit_velocity_30d ~ commits itself as proxy; stars_growth_30d ~ weekly diff of stars
    def _diff(seq: Sequence[float]) -> List[float]:
        if not seq:
            return []
        out = [seq[0]]
        for i in range(1, len(seq)):
            out.append(seq[i] - seq[i - 1])
        return out

    commits_vel = commits[:]  # proxy
    stars_growth = _diff(stars)

    # Attempt segment-wise stats
    m_stats = _segment_stats("mentions", company_id)
    c_stats = _segment_stats("commits", company_id)
    sg_stats = _segment_stats("stars", company_id)  # growth uses stars base for cohort
    f_stats = _segment_stats("filings", company_id)
    se_stats = _segment_stats("sentiment", company_id)

    z_mentions = _z(mentions, m_stats)
    z_commits = _z(commits_vel, c_stats)
    z_stars_g = _z(stars_growth, sg_stats)
    z_filings = _z(filings, f_stats)
    z_sent = _z(sentiment, se_stats)
    z_hiring = _z(hiring, None)
    z_pat = _z(patents, None)

    w_m = float(weights_cfg.get("mentions_7d", 0.35))
    w_c = float(weights_cfg.get("commit_velocity_30d", 0.25))
    w_sg = float(weights_cfg.get("stars_growth_30d", 0.15))
    w_f = float(weights_cfg.get("filings_90d", 0.15))
    w_se = float(weights_cfg.get("sentiment_30d", 0.10))
    w_hr = float(weights_cfg.get("hiring_rate_30d", 0.0))
    w_pt = float(weights_cfg.get("patent_count_90d", 0.0))
    S = [
        w_m * z_mentions[i]
        + w_c * z_commits[i]
        + w_sg * z_stars_g[i]
        + w_f * z_filings[i]
        + w_se * z_sent[i]
        + w_hr * z_hiring[i]
        + w_pt * z_pat[i]
        for i in range(len(dates))
    ]
    S_ema = _ema(S, alpha=alpha_cfg)
    series: List[Dict[str, object]] = []
    for i, d in enumerate(dates):
        components = {
            "z_mentions": z_mentions[i],
            "z_commits": z_commits[i],
            "z_stars_growth": z_stars_g[i],
            "z_filings": z_filings[i],
            "z_sentiment": z_sent[i],
            "z_hiring": z_hiring[i],
            "z_patents": z_pat[i],
            "S_raw": S[i],
            "S_ema": S_ema[i],
        }
        score = 50 + 25 * S_ema[i]
        # Clamp to [0, 100] to keep a stable contract
        score = 0.0 if score < 0 else (100.0 if score > 100.0 else score)
        series.append({"date": d, "signal_score": float(score), "components": components})
    _persist_signal_series(company_id, series)
    return series


def compute_alerts(company_id: int, window: str = "90d") -> List[Dict[str, object]]:
    """Simple alert generator based on signal_series deltas.
    - Emits an alert if day-over-day delta exceeds +1.0 in normalized units (~scaled here).
    """
    import uuid as _uuid
    trace_id = _uuid.uuid4().hex[:10]
    series = compute_signal_series(company_id, window)
    alerts: List[Dict[str, object]] = []
    if not series or len(series) < 2:
        return alerts
    # Compute std of S_ema from components to support a std-based threshold (ΔS_ema > 1.0 std)
    s_emas: List[float] = []
    try:
        for pt in series:
            comps = pt.get("components")
            if isinstance(comps, dict):
                s_emas.append(float((comps.get("S_ema", 0.0) or 0.0)))
            else:
                s_emas.append(0.0)
        mean_s = sum(s_emas) / len(s_emas)
        var_s = sum((x - mean_s) ** 2 for x in s_emas) / max(1, len(s_emas) - 1)
        std_s = var_s ** 0.5 if var_s > 0 else 0.0
    except Exception:
        std_s = 0.0

    prev = _safe_float(series[0].get("signal_score", 0.0), 0.0)
    for i, pt in enumerate(series[1:], start=1):
        cur = _safe_float(pt.get("signal_score", 0.0), 0.0)
        delta = float(cur) - float(prev)
        reason = "delta_gt_threshold"
        trigger = False
        delta_std = 0.0
        if std_s and len(series) >= 3:
            # Use std on S_ema components
            try:
                comps_prev: Any = series[i - 1].get("components") if i - 1 >= 0 else {}
                comps_cur: Any = pt.get("components")
                s_ema_prev = float((comps_prev.get("S_ema", 0.0) if isinstance(comps_prev, dict) else 0.0) or 0.0)
                s_ema_cur = float((comps_cur.get("S_ema", 0.0) if isinstance(comps_cur, dict) else 0.0) or 0.0)
                delta_std = (s_ema_cur - s_ema_prev) / (std_s or 1.0)
                trigger = delta_std > 1.0
                reason = "delta_gt_1std"
            except Exception:
                trigger = False
        if not trigger:
            # Use configured delta_threshold
            _, __, delta_thr = _load_signal_config()
            thr = float(delta_thr)
            trigger = delta > thr
            reason = "delta_gt_threshold"
        if trigger:
            # Build confidence score (0-1) from magnitude, evidence count, and stability
            try:
                recent = s_emas[max(0, i - 5) : i + 1]
                if recent:
                    m = sum(recent) / len(recent)
                    var_recent = sum((x - m) ** 2 for x in recent) / max(1, len(recent) - 1)
                else:
                    var_recent = 0.0
            except Exception:
                var_recent = 0.0
            # Evidence gathering (URLs only, keep persistence backward compatible)
            ev_urls: List[str] = []
            ev_objs: List[Dict[str, object]] = []
            try:
                from .db import Company  # type: ignore
                from .copilot import tool_retrieve_docs  # type: ignore
                with get_session() as s:  # type: ignore
                    c = s.get(Company, int(company_id))
                cname = getattr(c, "canonical_name", None) if c else None
                if cname:
                    urls = tool_retrieve_docs(f"{cname} product OR release OR funding OR hiring", limit=3)
                    if urls:
                        ev_urls = urls[:3]
                        for rank, u in enumerate(ev_urls, start=1):
                            ev_objs.append({"url": u, "rank": rank})
            except Exception:
                pass

            c1 = max(0.0, min(1.0, (delta_std - 1.0) / 2.0)) if std_s else 0.0
            c2 = max(0.0, min(1.0, len(ev_urls) / 3.0))
            c3 = max(0.0, min(1.0, 1.0 / (1.0 + (var_recent or 0.0))))
            confidence = round(0.6 * c1 + 0.25 * c2 + 0.15 * c3, 2)

            comps_any: Any = pt.get("components")
            components: Dict[str, float] = comps_any if isinstance(comps_any, dict) else {}
            # Build drivers string dynamically, including hiring/patents when material
            drv = [
                f"mentions {components.get('z_mentions', 0):+.2f}",
                f"commits {components.get('z_commits', 0):+.2f}",
                f"starsΔ {components.get('z_stars_growth', 0):+.2f}",
            ]
            try:
                # Include hiring/patents if weight > 0 or abs z >= 0.75
                w, _, __ = _load_signal_config()
                zh = float(components.get('z_hiring', 0) or 0)
                zp = float(components.get('z_patents', 0) or 0)
                if float(w.get('hiring_rate_30d', 0) or 0) > 0 or abs(zh) >= 0.75:
                    drv.append(f"hiring {zh:+.2f}")
                if float(w.get('patent_count_90d', 0) or 0) > 0 or abs(zp) >= 0.75:
                    drv.append(f"patents {zp:+.2f}")
            except Exception:
                pass
            explanation = (
                f"Signal up +{delta:.2f}; drivers: " + ", ".join(drv) + ". "
                + ("Crossed 1σ." if reason == "delta_gt_1std" else "Exceeded threshold.")
            )

            item = {
                "type": "threshold_crossing",
                "date": pt["date"],
                "score_delta": round(delta, 2),
                "reason": reason,
                "evidence_urls": ev_urls,
                # extras (not persisted in DB):
                "confidence": confidence,
                "explanation": explanation,
                "evidence": ev_objs,
                "trace_id": trace_id,
            }
            alerts.append(item)
        prev = cur
    # Optional: simple MAD-based anomaly on S_ema
    s_emas: List[float] = []
    try:
        if series and len(series) >= 7:
            s_emas = []
            for pt in series:
                comps = pt.get("components")
                if isinstance(comps, dict):
                    s_emas.append(float((comps.get("S_ema", 0.0) or 0.0)))
                else:
                    s_emas.append(0.0)
            med = sorted(s_emas)[len(s_emas)//2]
            deviations = [abs(x - med) for x in s_emas]
            mad = sorted(deviations)[len(deviations)//2] or 1.0
            last = s_emas[-1]
            ratio = abs(last - med) / (mad or 1.0)
            if ratio > 3.5:
                # Provide enriched fields to satisfy alert contract
                conf = max(0.0, min(1.0, (ratio - 3.5) / 3.0))
                alerts.append({
                    "type": "anomaly_signal",
                    "date": series[-1]["date"],
                    "score_delta": None,
                    "reason": "mad_gt_3.5",
                    "evidence_urls": [],
                    # enriched fields (not persisted):
                    "confidence": round(conf, 2),
                    "explanation": f"Signal anomaly detected (MAD ratio {ratio:.2f} > 3.5).",
                    "evidence": [],
                    "trace_id": trace_id,
                })
    except Exception:
        pass
    # Spike alerts (95th percentile) for filings and repo activity (commits or stars)
    try:
        rows = _fetch_cached_metrics(company_id, window)
        if rows:
            try:
                rows_sorted = sorted(rows, key=lambda r: getattr(r, "week_start", ""))
            except Exception:
                rows_sorted = rows
            def _p95(vals: List[float]) -> float:
                if not vals:
                    return 0.0
                vs = sorted(vals)
                k = int(0.95 * (len(vs) - 1))
                return float(vs[k])
            def _p95_window(vals: List[float], w: int = 8) -> float:
                if len(vals) <= 1:
                    return 0.0
                prev = vals[:-1]
                window = prev[-w:] if len(prev) > w else prev
                return _p95(window)
            filings = [float(getattr(r, "filings", 0) or 0) for r in rows_sorted]
            commits = [float(getattr(r, "commits", 0) or 0) for r in rows_sorted]
            stars = [float(getattr(r, "stars", 0) or 0) for r in rows_sorted]
            date_last = getattr(rows_sorted[-1], "week_start", "")
            # Filings spike
            if len(filings) >= 4 and filings[-1] > _p95_window(filings):
                # Confidence grows with exceedance factor over p95 window
                base = _p95_window(filings)
                factor = (float(filings[-1]) - float(base or 0.0)) / (float(base or 1.0))
                conf = max(0.0, min(1.0, 0.5 + 0.25 * factor))
                alerts.append({
                    "type": "filing_spike",
                    "date": date_last,
                    "score_delta": None,
                    "reason": "gt_p95",
                    "evidence_urls": [],
                    "confidence": round(conf, 2),
                    "explanation": "Unusual filings activity (> p95 of recent window).",
                    "evidence": [],
                    "trace_id": trace_id,
                })
            # Repo spike (commits or stars)
            if len(commits) >= 4 and commits[-1] > _p95_window(commits):
                base = _p95_window(commits)
                factor = (float(commits[-1]) - float(base or 0.0)) / (float(base or 1.0))
                conf = max(0.0, min(1.0, 0.5 + 0.25 * factor))
                alerts.append({
                    "type": "repo_spike",
                    "date": date_last,
                    "score_delta": None,
                    "reason": "gt_p95_commits",
                    "evidence_urls": [],
                    "confidence": round(conf, 2),
                    "explanation": "Repository commits spike (> p95 of recent window).",
                    "evidence": [],
                    "trace_id": trace_id,
                })
            elif len(stars) >= 4 and stars[-1] > _p95_window(stars):
                base = _p95_window(stars)
                factor = (float(stars[-1]) - float(base or 0.0)) / (float(base or 1.0))
                conf = max(0.0, min(1.0, 0.5 + 0.25 * factor))
                alerts.append({
                    "type": "repo_spike",
                    "date": date_last,
                    "score_delta": None,
                    "reason": "gt_p95_stars",
                    "evidence_urls": [],
                    "confidence": round(conf, 2),
                    "explanation": "Repository stars spike (> p95 of recent window).",
                    "evidence": [],
                    "trace_id": trace_id,
                })
    except Exception:
        pass
    _persist_alerts(company_id, alerts)
    return alerts
