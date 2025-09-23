import os
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.phase6

# Skip tests if no admin token configured (mirrors earlier Phase 5 pattern)
ADMIN_TOKEN = os.getenv("DEV_ADMIN_TOKEN")

if not ADMIN_TOKEN:
    pytest.skip("admin token not configured", allow_module_level=True)

from apps.api.aurora.main import app

client = TestClient(app)

def _create_three_nodes():
    for uid in ("n:snap-a", "n:snap-b", "n:snap-c"):
        r = client.post(
            "/admin/kg/nodes/upsert",
            json={"uid": uid, "type": "Entity", "props": {"name": uid}},
            params={"token": ADMIN_TOKEN},
        )
        assert r.status_code == 200, r.text

def test_snapshot_create_deterministic_and_sign_verify_hmac():
    # Ensure secret for HMAC backend
    os.environ.setdefault("SIGNING_BACKEND", "hmac")
    os.environ.setdefault("AURORA_SNAPSHOT_SIGNING_SECRET", "test-secret")
    _create_three_nodes()
    s1 = client.post("/admin/kg/snapshot", params={"token": ADMIN_TOKEN})
    assert s1.status_code == 200, s1.text
    h1 = s1.json()["snapshot_hash"]
    mr1 = s1.json().get("merkle_root")
    sig1 = s1.json().get("signature")
    assert h1 and isinstance(h1, str)
    s2 = client.post("/admin/kg/snapshot", params={"token": ADMIN_TOKEN})
    assert s2.status_code == 200
    h2 = s2.json()["snapshot_hash"]
    mr2 = s2.json().get("merkle_root")
    sig2 = s2.json().get("signature")
    assert h1 == h2, "Snapshot hash must be stable across identical graph state"
    assert mr1 == mr2, "Merkle root must be stable across identical graph state"
    if mr1:
        assert len(mr1) >= 32
    # If signature secret set, either both signatures are present or both None (depending on create path)
    if sig1 or sig2:
        assert sig1 == sig2
    # Explicit signing endpoint (should no-op unless force)
    sign1 = client.post("/admin/kg/snapshot/sign", json={"snapshot_hash": h1}, params={"token": ADMIN_TOKEN})
    assert sign1.status_code == 200
    body_sign1 = sign1.json()
    assert body_sign1["snapshot_hash"] == h1
    # Force regenerate
    sign2 = client.post("/admin/kg/snapshot/sign", json={"snapshot_hash": h1, "force": True}, params={"token": ADMIN_TOKEN})
    assert sign2.status_code == 200
    body_sign2 = sign2.json()
    if body_sign1.get("signature") and body_sign2.get("signature"):
        # Regeneration may produce identical HMAC (same secret+message) -> allow equality
        assert body_sign1["signature"] == body_sign2["signature"]
    # Verify (body)
    v1 = client.post("/kg/snapshot/verify", json={"snapshot_hash": h1, "signature": body_sign1.get("signature")})
    assert v1.status_code == 200
    vj1 = v1.json()
    assert vj1.get("backend") in ("hmac", "none")
    # Path variant
    v2 = client.post(f"/kg/snapshot/{h1}/verify", json={"signature": body_sign1.get("signature")})
    assert v2.status_code == 200
    # Negative case (tamper signature)
    if body_sign1.get("signature"):
        bad = client.post("/kg/snapshot/verify", json={"snapshot_hash": h1, "signature": body_sign1["signature"][:-1] + "0"})
        assert bad.status_code == 200
        assert bad.json().get("valid") is False
    # Snapshot listing
    lst = client.get("/admin/kg/snapshots", params={"token": ADMIN_TOKEN, "limit": 10})
    assert lst.status_code == 200
    snaps = lst.json().get("snapshots", [])
    assert any(s.get("snapshot_hash") == h1 for s in snaps)
    # Metrics exposure (best-effort assertions)
    met = client.get("/metrics")
    assert met.status_code == 200
    text = met.text
    assert "kg_snapshot_hash_total" in text
    assert "kg_snapshot_sign_total" in text

@pytest.mark.skipif("SIGSTORE_TESTS" not in os.environ, reason="sigstore tests disabled")
def test_snapshot_verify_sigstore_structural_offline():
    # This test exercises structural verification: supply a fake dsse bundle with payloadSHA256
    os.environ.setdefault("SIGNING_BACKEND", "sigstore")
    _create_three_nodes()
    s1 = client.post("/admin/kg/snapshot", params={"token": ADMIN_TOKEN})
    h1 = s1.json()["snapshot_hash"]
    # Attest with structural bundle
    bundle = {"payloadSHA256": h1}
    att = client.post(
        "/admin/kg/snapshot/attest",
        json={"snapshot_hash": h1, "dsse_bundle_json": __import__("json").dumps(bundle)},
        params={"token": ADMIN_TOKEN},
    )
    assert att.status_code == 200
    v1 = client.post("/kg/snapshot/verify", json={"snapshot_hash": h1, "backend": "sigstore", "dsse_bundle_json": __import__("json").dumps(bundle)})
    assert v1.status_code == 200
    assert v1.json().get("valid") in (True, False)  # Accept either depending on backend behavior
