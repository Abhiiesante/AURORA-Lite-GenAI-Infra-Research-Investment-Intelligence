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


def test_threshold_crossing_by_std(monkeypatch):
    # Build a series where S_ema jump exceeds 1 std between last two points
    weeks = [f"2025-07-{10+i:02d}" for i in range(7)]
    mentions = [5, 5, 5, 5, 5, 5, 50]  # cause uptick in z and S_ema at end
    rows = _mk_rows(weeks, mentions, filings_seq=[0]*7, stars_seq=[1,1,1,1,1,1,1], commits_seq=[1,1,1,1,1,1,1])
    monkeypatch.setattr(mx, "_fetch_cached_metrics", lambda company_id, window: rows)

    c = TestClient(main.app)
    r = c.get("/alerts/1?window=90d")
    assert r.status_code == 200
    alerts = r.json().get("alerts") or []
    assert any(a.get("type") == "threshold_crossing" for a in alerts)
