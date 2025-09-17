import json
import importlib.util
from pathlib import Path


def test_sigstore_offline_structural_verify(monkeypatch):
    # Test the verification helper directly to avoid FastAPI dependency
    monkeypatch.setenv("SIGNING_BACKEND", "sigstore")
    # Load signing.py directly to avoid importing the aurora package
    # tests -> api -> apps; we need apps/api/aurora/security/signing.py
    api_dir = Path(__file__).resolve().parents[1]
    signing_path = api_dir / "aurora" / "security" / "signing.py"
    spec = importlib.util.spec_from_file_location("signing_mod", str(signing_path))
    assert spec and spec.loader
    sigmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sigmod)  # type: ignore[arg-type]
    # Pretend sigstore optional dependency is available for the code path
    monkeypatch.setattr(sigmod, "_HAVE_SIGSTORE", True, raising=False)

    snapshot_hash = "deadbeefcafebabe"
    bundle = {"payloadSHA256": snapshot_hash}
    res = sigmod.verify_snapshot_signature(
        snapshot_hash=snapshot_hash,
        signature=None,
        backend="sigstore",
        cert_chain_pem=None,
        dsse_bundle_json=json.dumps(bundle),
        rekor_log_id=None,
        rekor_log_index=None,
    )
    assert res.get("backend") == "sigstore"
    assert res.get("valid") is True
    assert "structural" in (res.get("reason") or "")
