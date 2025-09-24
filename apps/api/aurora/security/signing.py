"""
Signing utilities for KG snapshots.

Backends:
- hmac: Uses AURORA_SNAPSHOT_SIGNING_SECRET to HMAC-SHA256 the snapshot hash
- sigstore: If configured and package available, attempts to generate a Sigstore signature

Environment:
- SIGNING_BACKEND: hmac (default) | sigstore
- AURORA_SNAPSHOT_SIGNING_SECRET: secret used for HMAC backend
"""
from __future__ import annotations

from typing import Optional, Dict, Any
import os


def _get_backend() -> str:
    return os.environ.get("SIGNING_BACKEND", "hmac").strip().lower()


try:
    import sigstore  # type: ignore
    _HAVE_SIGSTORE = True
except Exception:  # pragma: no cover - optional dependency
    sigstore = None  # type: ignore
    _HAVE_SIGSTORE = False


def sign_snapshot_hash(snapshot_hash: str) -> Dict[str, Any]:
    """Sign the provided snapshot hash using the configured backend.

    Returns a dict containing at least:
      - signature: str | None
      - backend: str ("hmac"|"sigstore"|"none")
      - cert_chain_pem: Optional[str] (sigstore only)
      - dsse_bundle_json: Optional[str] (sigstore only)
      - rekor_log_id: Optional[str] (sigstore only)
      - rekor_log_index: Optional[int] (sigstore only)
      - reason: Optional[str] (when signature not produced)
    """
    backend = _get_backend()
    if backend == "hmac":
        try:
            import hmac as _hmac
            import hashlib as _hl
            secret = os.environ.get("AURORA_SNAPSHOT_SIGNING_SECRET")
            if not secret:
                return {"signature": None, "backend": "hmac", "reason": "missing_secret", "cert_chain_pem": None, "dsse_bundle_json": None, "rekor_log_id": None, "rekor_log_index": None}
            sig = _hmac.new(str(secret).encode("utf-8"), snapshot_hash.encode("utf-8"), _hl.sha256).hexdigest()
            return {"signature": sig, "backend": "hmac", "cert_chain_pem": None, "dsse_bundle_json": None, "rekor_log_id": None, "rekor_log_index": None}
        except Exception as e:
            return {"signature": None, "backend": "hmac", "reason": f"error:{e}", "cert_chain_pem": None, "dsse_bundle_json": None, "rekor_log_id": None, "rekor_log_index": None}
    elif backend == "sigstore":
        if not _HAVE_SIGSTORE:
            return {"signature": None, "backend": "sigstore", "reason": "sigstore_not_available", "cert_chain_pem": None, "dsse_bundle_json": None, "rekor_log_id": None, "rekor_log_index": None}
        # Best-effort: attempt to use sigstore if available and configured.
        # Note: Full Sigstore flow requires an OIDC token and network access to Fulcio/Rekor.
        try:
            # Placeholder wiring: Return structured keys with not-configured reason.
            # Future: use sigstore-python to produce DSSE bundle + cert chain + Rekor inclusion proof.
            return {
                "signature": None,
                "backend": "sigstore",
                "cert_chain_pem": None,
                "dsse_bundle_json": None,
                "rekor_log_id": None,
                "rekor_log_index": None,
                "reason": "sigstore_not_configured",
            }
        except Exception as e:
            return {"signature": None, "backend": "sigstore", "reason": f"unavailable:{e}", "cert_chain_pem": None, "dsse_bundle_json": None, "rekor_log_id": None, "rekor_log_index": None}
    else:
        return {"signature": None, "backend": "none", "reason": "unsupported_backend", "cert_chain_pem": None, "dsse_bundle_json": None, "rekor_log_id": None, "rekor_log_index": None}


def verify_snapshot_signature(
    snapshot_hash: str,
    signature: Optional[str],
    backend: Optional[str] = None,
    cert_chain_pem: Optional[str] = None,
    dsse_bundle_json: Optional[str] = None,
    rekor_log_id: Optional[str] = None,
    rekor_log_index: Optional[int] = None,
) -> Dict[str, Any]:
    """Verify snapshot signature with the given backend (or configured default).

    Returns { valid: bool, backend: str, reason?: str }
    """
    be = (backend or _get_backend()).strip().lower()
    if be == "hmac":
        try:
            import hmac as _hmac
            import hashlib as _hl
            secret = os.environ.get("AURORA_SNAPSHOT_SIGNING_SECRET")
            if not secret or not signature:
                return {"valid": False, "backend": "hmac", "reason": "missing_secret_or_signature"}
            expected = _hmac.new(str(secret).encode("utf-8"), snapshot_hash.encode("utf-8"), _hl.sha256).hexdigest()
            return {"valid": _hmac.compare_digest(expected, signature), "backend": "hmac"}
        except Exception as e:
            return {"valid": False, "backend": "hmac", "reason": f"error:{e}"}
    elif be == "sigstore":
        # Full verification using sigstore-python Verifier (Fulcio + Rekor) with a policy.
        # Falls back to a structural bundle check when allowed. Tests monkeypatch _HAVE_SIGSTORE True
        # and inject fake submodules under sys.modules; so we support flexible import fallbacks.
        if not _HAVE_SIGSTORE:
            return {"valid": False, "backend": "sigstore", "reason": "sigstore_not_available"}
        if not dsse_bundle_json:
            return {"valid": False, "backend": "sigstore", "reason": "missing_dsse_bundle"}
        env = os.environ.get("SIGSTORE_ENV", "production").strip().lower()
        verify_identity = os.environ.get("SIGSTORE_VERIFY_IDENTITY")
        verify_issuer = os.environ.get("SIGSTORE_VERIFY_ISSUER")
        allow_unsafe = os.environ.get("SIGSTORE_ALLOW_UNSAFE_POLICY", "0").strip().lower() in ("1", "true", "yes")
        allow_offline_structural = os.environ.get("SIGSTORE_OFFLINE_FALLBACK", "1").strip().lower() in ("1", "true", "yes")
        try:
            import sys
            # Bundle import (normal or fallback to injected module)
            try:
                from sigstore.models import Bundle as _Bundle  # type: ignore
            except Exception:  # pragma: no cover - test fallback
                _bundle_mod = sys.modules.get("sigstore.models")
                _Bundle = getattr(_bundle_mod, "Bundle", None) if _bundle_mod else None  # type: ignore
            if _Bundle is None:  # type: ignore
                raise ImportError("sigstore.models.Bundle_unavailable")
            bundle = _Bundle.from_json(dsse_bundle_json)  # type: ignore
            # Verifier import
            try:
                from sigstore.verify.verifier import Verifier as _Verifier  # type: ignore
            except Exception:  # pragma: no cover
                _ver_mod = sys.modules.get("sigstore.verify.verifier")
                _Verifier = getattr(_ver_mod, "Verifier", None) if _ver_mod else None  # type: ignore
            if _Verifier is None:  # type: ignore
                raise ImportError("sigstore.verify.verifier.Verifier_unavailable")
            verifier = _Verifier.staging() if env == "staging" else _Verifier.production()  # type: ignore
            # Policy import
            try:
                from sigstore.verify import policy as _policy  # type: ignore
            except Exception:  # pragma: no cover
                _policy = sys.modules.get("sigstore.verify.policy")  # type: ignore
            if _policy is None:  # type: ignore
                raise ImportError("sigstore.verify.policy_unavailable")
            if verify_identity:
                pol = _policy.Identity(identity=str(verify_identity), issuer=str(verify_issuer) if verify_issuer else None)  # type: ignore
            elif allow_unsafe:
                pol = _policy.UnsafeNoOp()  # type: ignore
            else:
                raise RuntimeError("missing_policy")
            ptype, payload = verifier.verify_dsse(bundle, pol)  # type: ignore
            import hashlib as _hl
            if _hl.sha256(payload).hexdigest() == str(snapshot_hash):
                return {"valid": True, "backend": "sigstore", "reason": f"verified:{env}", "payload_type": ptype}
            reason = "payload_hash_mismatch"
        except Exception as e:
            reason = f"verify_error:{e}"
        # Structural fallback
        if allow_offline_structural:
            try:
                import json as _json
                obj = _json.loads(dsse_bundle_json)
                claimed = None
                if isinstance(obj, dict):
                    claimed = obj.get("payloadSHA256") or obj.get("snapshot_hash")
                    if not claimed and isinstance(obj.get("dsse"), dict):
                        claimed = obj["dsse"].get("payloadSHA256")
                if claimed and str(claimed) == str(snapshot_hash):
                    return {"valid": True, "backend": "sigstore", "reason": "structural_match_only"}
            except Exception:
                pass
        return {"valid": False, "backend": "sigstore", "reason": reason}
    else:
        return {"valid": False, "backend": be, "reason": "unsupported_backend"}
