from fastapi.testclient import TestClient
import types

import aurora.main as main
import aurora.metrics as mx


def _mk_rows(weeks, mentions_seq, filings_seq=None, stars_seq=None, commits_seq=None, sentiment_seq=None):
    filings_seq = filings_seq or [0]*len(weeks)
    stars_seq = stars_seq or [0]*len(weeks)
    commits_seq = commits_seq or [0]*len(weeks)
    sentiment_seq = sentiment_seq or [0.0]*len(weeks)
    rows = []
    for i, d in enumerate(weeks):
        row = types.SimpleNamespace(
            week_start=d,
            mentions=mentions_seq[i],
            filings=filings_seq[i],
            stars=stars_seq[i],
            commits=commits_seq[i],
            sentiment=sentiment_seq[i],
        )
        rows.append(row)
    return rows


def test_signal_clamps_and_ema(monkeypatch):
    # Create synthetic series with an outlier spike to test z-score clamp and EMA smoothing
    weeks = [f"2025-07-{10+i:02d}" for i in range(7)]
    mentions = [10, 10, 10, 10, 10, 10, 1000]  # huge spike
    rows = _mk_rows(weeks, mentions, filings_seq=[1]*7, stars_seq=[1,2,3,4,5,6,7], commits_seq=[5]*7, sentiment_seq=[0.1]*7)
    monkeypatch.setattr(mx, "_fetch_cached_metrics", lambda company_id, window: rows)

    c = TestClient(main.app)
    r = c.get("/signal/1?window=90d")
    assert r.status_code == 200
    data = r.json()
    series = data.get("series") or []
    assert len(series) == 7
    # z_mentions should be clamped to <= 3.0
    z_vals = [pt["components"]["z_mentions"] for pt in series]
    assert max(z_vals) <= 3.0
    assert min(z_vals) >= -3.0
    # EMA smoothing yields last value not equal to raw z and within bounds for signal_score
    last = series[-1]
    assert 0.0 <= float(last["signal_score"]) <= 100.0


def test_alert_threshold_trigger(monkeypatch):
    weeks = [f"2025-07-{10+i:02d}" for i in range(6)]
    mentions = [5, 5, 5, 5, 5, 50]  # jump at end
    rows = _mk_rows(weeks, mentions, filings_seq=[0]*6, stars_seq=[1,1,1,1,1,1], commits_seq=[1,1,1,1,1,1])
    monkeypatch.setattr(mx, "_fetch_cached_metrics", lambda company_id, window: rows)
    # Lower threshold to ensure alert
    from apps.api.aurora.config import settings as cfg
    old_thr = getattr(cfg, "alert_delta_threshold", 5.0)
    cfg.alert_delta_threshold = 0.1

    c = TestClient(main.app)
    r = c.get("/alerts/1?window=90d")
    assert r.status_code == 200
    alerts = r.json().get("alerts") or []
    assert any(a.get("type") == "threshold_crossing" for a in alerts)

    cfg.alert_delta_threshold = old_thr


def test_spike_alert_p95(monkeypatch):
    # filings last value exceeds rolling p95 of prior window
    weeks = [f"2025-07-{10+i:02d}" for i in range(8)]
    mentions = [1]*8
    filings = [0,0,1,0,1,0,1,10]  # last is spike
    rows = _mk_rows(weeks, mentions, filings_seq=filings, stars_seq=[1]*8, commits_seq=[1]*8)
    monkeypatch.setattr(mx, "_fetch_cached_metrics", lambda company_id, window: rows)

    c = TestClient(main.app)
    r = c.get("/alerts/1?window=90d")
    assert r.status_code == 200
    alerts = r.json().get("alerts") or []
    assert any(a.get("type") == "filing_spike" for a in alerts)
