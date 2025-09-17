from __future__ import annotations

import os
import sys

# Allow importing the package
sys.path.insert(0, os.getcwd())

from apps.api.aurora.retrieval import _meili_search, _qdrant_search, hybrid


def run_for_tenant(tid: str) -> bool:
    os.environ["AURORA_DEFAULT_TENANT_ID"] = tid
    m = _meili_search("competition")
    q = _qdrant_search("competition")
    h = hybrid("competition")
    print(f"tenant={tid} meili={len(m)} qdrant={len(q)} hybrid={len(h)}")
    ok = bool(m or q or h)
    # Ensure only this tenant's payloads are present (best-effort check)
    def only_tid(items):
        for it in items:
            tags = it.get("tags", [])
            if any(str(t).startswith("tenant:") and str(t) != f"tenant:{tid}" for t in tags):
                return False
        return True
    return ok and only_tid(q) and only_tid(h)


if __name__ == "__main__":
    t1 = run_for_tenant("1")
    t2 = run_for_tenant("2")
    if not (t1 and t2):
        print("SMOKE_FAIL: tenant retrieval isolation failed", file=sys.stderr)
        sys.exit(1)
    print("SMOKE_OK: tenant retrieval isolation")
