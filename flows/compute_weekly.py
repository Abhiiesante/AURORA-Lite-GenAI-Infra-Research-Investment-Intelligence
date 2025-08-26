from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from prefect import flow, task, get_run_logger

from apps.api.aurora.db import (
    get_session,
    init_db,
    Company,
    SignalSnapshot,
    Alert,
)
from apps.api.aurora.metrics import compute_signal_series, compute_alerts


@task
def _list_company_ids() -> List[int]:
    init_db()
    ids: List[int] = []
    try:
        with get_session() as s:
            rows = list(s.exec("SELECT id FROM companies"))  # type: ignore[arg-type]
            for r in rows:
                ids.append(int(r[0] if isinstance(r, (tuple, list)) else getattr(r, "id", 0)))
    except Exception:
        # empty list is fine; downstream will no-op
        pass
    return ids


@task
def _persist_latest_signal(company_id: int) -> int:
    init_db()
    try:
        series = compute_signal_series(company_id, window="180d") or []  # type: ignore[call-arg]
    except Exception:
        series = []
    if not series:
        return 0
    latest = series[-1]
    score = float(latest.get("signal_score") or latest.get("value") or 0.0)
    week_start = latest.get("week_start") or latest.get("date") or datetime.now(timezone.utc).date().isoformat()
    try:
        with get_session() as s:
            snap = SignalSnapshot(company_id=company_id, week_start=str(week_start), signal_score=score, components_json=None)
            s.add(snap)  # type: ignore[attr-defined]
            s.commit()  # type: ignore[attr-defined]
        return 1
    except Exception:
        return 0


@task
def _persist_alerts(company_id: int) -> int:
    init_db()
    try:
        alerts = compute_alerts(company_id) or []  # type: ignore[call-arg]
    except Exception:
        alerts = []
    count = 0
    try:
        with get_session() as s:
            for a in alerts:
                obj = Alert(
                    company_id=company_id,
                    type=str(a.get("type") or "threshold"),
                    score_delta=a.get("delta"),
                    reason=a.get("reason"),
                    evidence_urls=None,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                s.add(obj)  # type: ignore[attr-defined]
                count += 1
            s.commit()  # type: ignore[attr-defined]
    except Exception:
        return 0
    return count


@flow(name="compute_weekly_signals_and_alerts")
def compute_weekly() -> dict:
    """Compute latest signal snapshot and persist new alerts for all companies.

    Safe to run with an empty DB; no-ops gracefully.
    """
    logger = get_run_logger()
    ids = _list_company_ids()
    if not ids:
        logger.info("No companies found; skipping signal/alert computation.")
        return {"companies": 0, "snapshots": 0, "alerts": 0}
    snap_total = 0
    alert_total = 0
    for cid in ids:
        snap_total += _persist_latest_signal.submit(cid).result()
        alert_total += _persist_alerts.submit(cid).result()
    out = {"companies": len(ids), "snapshots": snap_total, "alerts": alert_total}
    logger.info(f"Weekly compute done: {out}")
    return out


if __name__ == "__main__":
    print(compute_weekly())
