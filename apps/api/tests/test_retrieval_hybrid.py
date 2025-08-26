from aurora import retrieval


def test_rrf_fuse_and_token_rerank_no_backends():
    # When no backends, rrf_fuse should handle empty lists and token rerank should return subset
    fused = retrieval.rrf_fuse([[], []])
    assert fused == []

    docs = [
        {"id": "1", "text": "alpha beta", "url": "u1", "tags": []},
        {"id": "2", "text": "gamma delta", "url": "u2", "tags": []},
    ]
    ranked = retrieval._token_rerank("alpha", docs, top_k=1)
    assert len(ranked) == 1 and ranked[0]["id"] == "1"
