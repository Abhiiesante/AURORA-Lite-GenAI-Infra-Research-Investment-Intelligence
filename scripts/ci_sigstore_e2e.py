"""
CI E2E for Sigstore verification flow (offline-friendly):
- Creates a KG snapshot via /admin/kg/snapshot
- Constructs a minimal DSSE-like bundle that claims payloadSHA256 == snapshot_hash (structural)
- Calls /kg/snapshot/verify with SIGNING_BACKEND=sigstore to verify (should pass via structural fallback)
- Attaches the bundle via /admin/kg/snapshot/attest
- Calls /kg/snapshot/verify again without providing bundle; server should read from DB and verify

Note: This uses FastAPI TestClient in-process to avoid external network.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Any

from apps.api.aurora.main import app  # type: ignore
from fastapi.testclient import TestClient  # type: ignore


def _as_admin_headers() -> Dict[str, str]:
    tok = os.environ.get("DEV_ADMIN_TOKEN", "adm1")
    return {"X-Admin-Token": tok}


def main():
    # Ensure backend is sigstore to hit the sigstore path with structural fallback
    os.environ.setdefault("SIGNING_BACKEND", "sigstore")
    os.environ.setdefault("SIGSTORE_OFFLINE_FALLBACK", "1")

    c = TestClient(app)
    # 1) Create snapshot
    r = c.post("/admin/kg/snapshot", params={"token": os.environ.get("DEV_ADMIN_TOKEN", "adm1")}, json={"notes": "ci-e2e"})
    assert r.status_code == 200, r.text
    j = r.json()
    snapshot_hash = j["snapshot_hash"]

    # 2) Build minimal structural bundle
    bundle = {
        "payloadSHA256": snapshot_hash,
        "dsse": {
            "payloadType": "application/vnd.aio.kg+json",
            # Omit actual signatures to keep offline
        },
    }
    # 3) Verify with bundle provided
    body = {"snapshot_hash": snapshot_hash, "backend": "sigstore", "dsse_bundle_json": json.dumps(bundle)}
    r2 = c.post("/kg/snapshot/verify", json=body)
    assert r2.status_code == 200, r2.text
    j2 = r2.json()
    assert j2.get("valid") is True, j2

    # 4) Attach via attest
    att = {
        "snapshot_hash": snapshot_hash,
        "dsse_bundle_json": json.dumps(bundle),
        "signature_backend": "sigstore",
    }
    r3 = c.post("/admin/kg/snapshot/attest", params={"token": os.environ.get("DEV_ADMIN_TOKEN", "adm1")}, json=att)
    assert r3.status_code == 200, r3.text

    # 5) Verify again without bundle (server should find it in DB)
    r4 = c.post("/kg/snapshot/verify", json={"snapshot_hash": snapshot_hash, "backend": "sigstore"})
    assert r4.status_code == 200, r4.text
    j4 = r4.json()
    assert j4.get("valid") is True, j4

    print("sigstore E2E (structural) passed for", snapshot_hash)


if __name__ == "__main__":
    main()
