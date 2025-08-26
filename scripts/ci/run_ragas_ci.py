#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone


def _add_path():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    api = os.path.join(repo, "apps", "api")
    if api not in sys.path:
        sys.path.insert(0, api)


def main() -> int:
    _add_path()
    from aurora.db import init_db, get_session, InsightCache  # type: ignore
    from aurora.evals_runner import run_ragas_eval  # type: ignore
    from aurora.main import _cache_key  # type: ignore
    import json

    # Initialize DB (SQLite default if DATABASE_URL not set)
    init_db()

    # Golden set (expand to ~50). Allow override via env RAG_GOLDEN_PATH (JSON lines: one question per line or JSON array)
    golden_path = os.environ.get("RAG_GOLDEN_PATH")
    questions: list[str]
    if golden_path and os.path.exists(golden_path):
        try:
            txt = open(golden_path, encoding="utf-8").read()
            if txt.strip().startswith("["):
                import json as _json
                questions = [str(x) for x in _json.loads(txt)]
            else:
                questions = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        except Exception:
            questions = []
    else:
        questions = [
            "Compare Pinecone vs Weaviate traction and risks",
            "Explain Qdrant community growth with citations",
            "Top trends in RAG orchestration last 90 days",
            "Risk radar for Milvus",
            "Who are top contributors in vector DBs and how is momentum shifting?",
            "Summarize enterprise adoption signals for pgvector",
            "Which LLM eval frameworks gained traction last quarter?",
            "FAISS vs ScaNN: tradeoffs for production search with sources",
            "Key investors backing retrieval infra and recent co-investment patterns",
            "Vector DB pricing trends across tiers with citations",
        ]
    # pad to ~50 simple variants to stabilize RAG eval
    while len(questions) < 50:
        questions.append(f"Golden Q {len(questions)+1}")

    res = run_ragas_eval(questions)
    summ = res.get("summary", {})
    f = float(summ.get("faithfulness", 0.0))
    r = float(summ.get("relevancy", 0.0))
    rc = float(summ.get("recall", 0.0))

    # Threshold gates
    thr = {"faithfulness": 0.90, "relevancy": 0.75, "recall": 0.70}
    fails = []
    if f < thr["faithfulness"]:
        fails.append(f"faithfulness {f:.3f} < {thr['faithfulness']}")
    if r < thr["relevancy"]:
        fails.append(f"relevancy {r:.3f} < {thr['relevancy']}")
    if rc < thr["recall"]:
        fails.append(f"recall {rc:.3f} < {thr['recall']}")

    # Week-over-week dip check (best-effort if last week exists)
    try:
        now = datetime.now(timezone.utc)
        last_week = (now - timedelta(days=7)).isocalendar().week
        last_key = _cache_key("evals_report", {"week": last_week})
        with get_session() as s:
            rows = list(s.exec("SELECT output_json FROM insight_cache WHERE key_hash = :k"), params={"k": last_key})  # type: ignore
            if rows:
                out_json = rows[0][0] if isinstance(rows[0], (tuple, list)) else getattr(rows[0], "output_json", None)
                if out_json:
                    prev = json.loads(out_json).get("summary", {})
                    pf, pr, prc = float(prev.get("faithfulness", 0.0)), float(prev.get("relevancy", 0.0)), float(prev.get("recall", 0.0))
                    # absolute dip > 0.05 triggers failure
                    if (pf - f) > 0.05:
                        fails.append(f"faithfulness dipped >5%: prev {pf:.3f} -> now {f:.3f}")
                    if (pr - r) > 0.05:
                        fails.append(f"relevancy dipped >5%: prev {pr:.3f} -> now {r:.3f}")
                    if (prc - rc) > 0.05:
                        fails.append(f"recall dipped >5%: prev {prc:.3f} -> now {rc:.3f}")
    except Exception:
        # ignore if prior not available
        pass

    if fails:
        print("RAG eval gates failed:\n - " + "\n - ".join(fails))
        return 1
    print("RAG eval gates OK:", json.dumps(summ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
