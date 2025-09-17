from __future__ import annotations

import os
import sys
from typing import Any

from fastapi.testclient import TestClient

# Ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from apps.api.aurora.main import app  # noqa: E402


def main() -> int:
    ok = True
    with TestClient(app) as client:
        # Admin token guard may be enabled; try to read from env
        tok = os.environ.get("DEV_ADMIN_TOKEN")
        headers = {"x-dev-token": tok} if tok else {}
        # Upsert a tiny KG edge-less snapshot is fine; the endpoint reads current state
        r = client.post("/admin/kg/snapshot", json={"notes": "smoke"}, headers=headers)
        print("POST /admin/kg/snapshot ->", r.status_code)
        if r.status_code not in (200, 201):
            print(r.text)
            return 1
        data: dict[str, Any] = r.json()
        snap_hash = data.get("snapshot_hash") or data.get("hash")
        if not snap_hash:
            print("missing snapshot hash in response")
            return 1
        # Verify
        body = {"snapshot_hash": snap_hash}
        if data.get("signature"):
            body["signature"] = data.get("signature")
        if data.get("signature_backend"):
            body["backend"] = data.get("signature_backend")
        if data.get("dsse_bundle_json"):
            body["dsse_bundle_json"] = data.get("dsse_bundle_json")
        r2 = client.post("/kg/snapshot/verify", json=body)
        print("POST /kg/snapshot/verify ->", r2.status_code, r2.json())
        if r2.status_code != 200 or not r2.json().get("valid", False):
            print("verification failed")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
