#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys


def _add_path():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    api = os.path.join(repo, "apps", "api")
    if api not in sys.path:
        sys.path.insert(0, api)


def main() -> int:
    _add_path()
    try:
        from aurora.db import init_db  # type: ignore
        from aurora.evals_runner import run_ragas_eval  # type: ignore
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"import failed: {e}"}))
        return 0

    try:
        init_db()
    except Exception:
        pass

    questions = [
        "Pinecone traction",
        "Weaviate traction",
        "Qdrant risks",
        "Top trends in vector DBs",
        "Milvus community growth",
    ]
    try:
        res = run_ragas_eval(questions)
        summ = res.get("summary", {})
        out = {
            "ok": True,
            "summary": {
                "faithfulness": float(summ.get("faithfulness", 0.0)),
                "relevancy": float(summ.get("relevancy", 0.0)),
                "recall": float(summ.get("recall", 0.0)),
            },
            "note": res.get("note"),
        }
        print(json.dumps(out))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
