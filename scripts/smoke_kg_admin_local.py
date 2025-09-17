import os
import sys
from typing import Any

from fastapi.testclient import TestClient

# Ensure repo root is on sys.path when running as a script
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def main() -> int:
    token = os.environ.get("DEV_ADMIN_TOKEN")
    if not token:
        print("ERROR: DEV_ADMIN_TOKEN is not set in the environment.", file=sys.stderr)
        return 2

    try:
        from apps.api.aurora.main import app  # local import to honor env settings
    except Exception as e:  # pragma: no cover
        print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
        return 2

    client = TestClient(app)

    def _post(path: str, json: dict[str, Any]):
        r = client.post(path, json=json, params={"token": token})
        if r.status_code != 200:
            print(f"FAIL POST {path}: {r.status_code} {r.text}", file=sys.stderr)
            raise SystemExit(1)
        return r

    def _get(path: str):
        r = client.get(path, params={"token": token})
        if r.status_code != 200:
            print(f"FAIL GET {path}: {r.status_code} {r.text}", file=sys.stderr)
            raise SystemExit(1)
        return r

    # Upsert two nodes
    r1 = _post("/admin/kg/nodes/upsert", {"uid": "n:alpha", "type": "Company", "props": {"name": "Alpha"}})
    r2 = _post("/admin/kg/nodes/upsert", {"uid": "n:beta", "type": "Company", "props": {"name": "Beta"}})
    print("nodes upsert:", r1.json(), "|", r2.json())

    # List nodes
    r3 = _get("/admin/kg/nodes")
    print("nodes list count:", len(r3.json().get("nodes", [])))

    # Upsert edge
    r4 = _post("/admin/kg/edges/upsert", {"src_uid": "n:alpha", "dst_uid": "n:beta", "type": "REL"})
    print("edge upsert:", r4.json())

    # List edges
    r5 = _get("/admin/kg/edges")
    print("edges list count:", len(r5.json().get("edges", [])))

    print("OK: admin KG local smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
