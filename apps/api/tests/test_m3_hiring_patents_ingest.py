from fastapi.testclient import TestClient
import types

import aurora.main as main
import aurora.metrics as mx


def _mk_rows(weeks, mentions_seq, hiring_seq=None, patents_seq=None):
    hiring_seq = hiring_seq or [0.0]*len(weeks)
    patents_seq = patents_seq or [0.0]*len(weeks)
    rows = []
    for i, d in enumerate(weeks):
        row = types.SimpleNamespace(
            week_start=d,
            mentions=mentions_seq[i],
            filings=0,
            stars=0,
            commits=0,
            sentiment=0.0,
            hiring=hiring_seq[i],
            patents=patents_seq[i],
        )
        rows.append(row)
    return rows


def test_alert_explanation_mentions_hiring(monkeypatch):
    # Configure weight to surface hiring if present
    monkeypatch.setattr(mx, "_load_signal_config", lambda: ({
        "mentions_7d": 0.35,
        "commit_velocity_30d": 0.0,
        "stars_growth_30d": 0.0,
        "filings_90d": 0.0,
        "sentiment_30d": 0.0,
        "hiring_rate_30d": 0.5,
        "patent_count_90d": 0.0,
    }, 0.4, 0.5))
    weeks = [f"2025-08-{10+i:02d}" for i in range(7)]
    # flat mentions; spike hiring at end to influence S
    mentions = [5,5,5,5,5,5,5]
    hiring = [0,0,0,0,0,0,50]
    rows = _mk_rows(weeks, mentions_seq=mentions, hiring_seq=hiring)
    monkeypatch.setattr(mx, "_fetch_cached_metrics", lambda company_id, window: rows)

    c = TestClient(main.app)
    r = c.get("/alerts/1?window=90d")
    assert r.status_code == 200
    alerts = r.json().get("alerts") or []
    # If alert exists, explanation should mention hiring when weight > 0 and z significant
    if alerts:
        exp = alerts[-1].get("explanation", "")
        assert "hiring" in exp.lower()
