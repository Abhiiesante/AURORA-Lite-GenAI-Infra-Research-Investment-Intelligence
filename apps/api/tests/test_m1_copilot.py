import aurora.copilot as cp


def test_rrf_fuse_merges_and_limits():
    dense = ["u1", "u2", "u3"]
    sparse = ["u3", "u4", "u5"]
    out = cp.rrf_fuse(dense, sparse, k=60, top_n=3)
    assert len(out) == 3
    assert "u3" in out  # appears in both


def test_detect_company_ids_handles_no_db(monkeypatch):
    monkeypatch.setattr(cp, "_candidate_company_ids", lambda: [(1, "ExampleAI"), (2, "OtherCo")])
    ids = cp.detect_company_ids("Compare ExampleAI and OtherCo", top_k=2)
    assert ids[:2] == [1, 2]
