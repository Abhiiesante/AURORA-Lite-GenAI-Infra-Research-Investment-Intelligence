from fastapi.testclient import TestClient
import types

import aurora.main as main
import aurora.metrics as mx


def _mk_rows(weeks, vals):
    rows = []
    for i, d in enumerate(weeks):
        rows.append(types.SimpleNamespace(
            week_start=d,
            mentions=1,
            filings=0,
            stars=0,
            commits=0,
            sentiment=0.0,
            hiring=vals[i],
            patents=0.0,
            signal_score=50.0,
        ))
    return rows


def test_dashboard_includes_hiring_when_present(monkeypatch):
    weeks = [f"2025-08-{10+i:02d}" for i in range(4)]
    rows = _mk_rows(weeks, vals=[0.0, 0.0, 1.0, 2.0])
    monkeypatch.setattr(mx, "_fetch_cached_metrics", lambda company_id, window: rows)
    c = TestClient(main.app)
    r = c.get("/company/1/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert "hiring_30d" in data.get("kpis", {})
    sl = data.get("sparklines") or []
    assert any(s.get("metric") == "hiring_30d" for s in sl)
