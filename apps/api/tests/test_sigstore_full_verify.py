import importlib.util
from pathlib import Path


class _FakeBundle:
    @classmethod
    def from_json(cls, raw):  # pragma: no cover - trivial
        return cls()


class _FakeVerifier:
    @classmethod
    def production(cls):  # pragma: no cover - trivial
        return cls()

    @classmethod
    def staging(cls):  # pragma: no cover - trivial
        return cls()

    def verify_dsse(self, bundle, policy):
        # Return a payload that is the ASCII form of the snapshot hash, so its sha256 equals the hex string only
        # when the snapshot hash is itself the sha256 of that ASCII string. We'll override the function to match.
        # Tests will monkeypatch this method directly to return the desired payload.
        raise NotImplementedError


class _FakePolicy:
    class Identity:
        def __init__(self, identity: str, issuer: str | None = None):
            self.identity = identity
            self.issuer = issuer

    class UnsafeNoOp:
        pass


def _load_signing_module():
    api_dir = Path(__file__).resolve().parents[1]
    signing_path = api_dir / "aurora" / "security" / "signing.py"
    spec = importlib.util.spec_from_file_location("signing_mod", str(signing_path))
    assert spec and spec.loader
    sigmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sigmod)  # type: ignore[arg-type]
    return sigmod


def test_sigstore_full_verify_identity_policy(monkeypatch):
    sigmod = _load_signing_module()
    # Pretend sigstore is available and wire fake classes
    monkeypatch.setattr(sigmod, "_HAVE_SIGSTORE", True, raising=False)

    # Provide fake sigstore modules in the expected import locations
    import types, sys

    fake_models = types.SimpleNamespace(Bundle=_FakeBundle)
    fake_verifier_mod = types.SimpleNamespace(Verifier=_FakeVerifier)
    fake_policy_mod = _FakePolicy

    sys.modules["sigstore.models"] = fake_models  # type: ignore
    sys.modules["sigstore.verify.verifier"] = fake_verifier_mod  # type: ignore
    sys.modules["sigstore.verify.policy"] = fake_policy_mod  # type: ignore

    # Make verify_dsse return a payload whose sha256 equals the provided snapshot hash
    import hashlib

    payload = b"hello world"
    snapshot_hash = hashlib.sha256(payload).hexdigest()

    def _verify_dsse(self, bundle, policy):  # type: ignore[no-redef]
        assert isinstance(policy, _FakePolicy.Identity)
        return ("application/vnd.test", payload)

    monkeypatch.setattr(_FakeVerifier, "verify_dsse", _verify_dsse, raising=False)

    res = sigmod.verify_snapshot_signature(
        snapshot_hash=snapshot_hash,
        signature=None,
        backend="sigstore",
        cert_chain_pem=None,
        dsse_bundle_json="{}",
        rekor_log_id=None,
        rekor_log_index=None,
    )
    assert res.get("backend") == "sigstore"
    assert res.get("valid") is False  # missing policy

    # Now set identity policy via env and try again
    monkeypatch.setenv("SIGSTORE_VERIFY_IDENTITY", "mailto:someone@example.com")
    monkeypatch.delenv("SIGSTORE_ALLOW_UNSAFE_POLICY", raising=False)
    res2 = sigmod.verify_snapshot_signature(
        snapshot_hash=snapshot_hash,
        signature=None,
        backend="sigstore",
        cert_chain_pem=None,
        dsse_bundle_json="{}",
        rekor_log_id=None,
        rekor_log_index=None,
    )
    assert res2.get("valid") is True
    assert "verified:" in res2.get("reason", "")


def test_sigstore_full_verify_unsafe_policy(monkeypatch):
    sigmod = _load_signing_module()
    monkeypatch.setattr(sigmod, "_HAVE_SIGSTORE", True, raising=False)

    import types, sys, hashlib

    sys.modules["sigstore.models"] = types.SimpleNamespace(Bundle=_FakeBundle)  # type: ignore
    sys.modules["sigstore.verify.verifier"] = types.SimpleNamespace(Verifier=_FakeVerifier)  # type: ignore
    sys.modules["sigstore.verify.policy"] = _FakePolicy  # type: ignore

    payload = b"phase5"
    snapshot_hash = hashlib.sha256(payload).hexdigest()

    def _verify_dsse(self, bundle, policy):  # type: ignore[no-redef]
        assert isinstance(policy, _FakePolicy.UnsafeNoOp)
        return ("application/test", payload)

    monkeypatch.setattr(_FakeVerifier, "verify_dsse", _verify_dsse, raising=False)

    # No identity provided; allow unsafe policy via env
    monkeypatch.setenv("SIGSTORE_ALLOW_UNSAFE_POLICY", "1")
    res = sigmod.verify_snapshot_signature(
        snapshot_hash=snapshot_hash,
        signature=None,
        backend="sigstore",
        cert_chain_pem=None,
        dsse_bundle_json="{}",
        rekor_log_id=None,
        rekor_log_index=None,
    )
    assert res.get("valid") is True
    assert "verified:" in res.get("reason", "")
