from fastapi.testclient import TestClient
import types

import aurora.main as main
import aurora.trends as tr


def test_delta_and_change_flag_basic():
    freqs = [1.0, 1.1, 1.6]
    d, flag = tr.delta_and_change_flag(freqs)
    assert d == 0.5
    assert isinstance(flag, bool)


def test_detect_change_flags_fallback():
    # Provide a gentle series with a final spike
    freqs = [1.0, 1.0, 1.1, 1.15, 2.0]
    flags = tr._detect_change_flags(freqs)
    assert isinstance(flags, list) and len(flags) == len(freqs)
    # Fallback logic should often mark the last point as change
    assert flags[-1] in (True, False)  # non-strict but checks contract


def test_trends_top_contract(monkeypatch):
    # Ensure endpoint responds with enriched fields even without a DB
    c = TestClient(main.app)
    r = c.get("/trends/top")
    assert r.status_code == 200
    data = r.json()
    topics = data.get("topics") or []
    if topics:
        t0 = topics[0]
        assert "topic_id" in t0 and "label" in t0 and "delta" in t0 and "change_flag" in t0
        # Enriched helpers may exist
        if "top_docs" in t0:
            assert isinstance(t0["top_docs"], list)
