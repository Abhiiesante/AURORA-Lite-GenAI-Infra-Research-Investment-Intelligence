import os
import sys
import pytest

# Skip by default unless explicitly enabled
RUN_SMOKE = (os.getenv("AURORA_RUN_TENANT_SMOKE") or "").strip().lower() in ("1", "true", "yes")

@pytest.mark.skipif(not RUN_SMOKE, reason="tenant smoke disabled; set AURORA_RUN_TENANT_SMOKE=1 to enable")
def test_tenant_retrieval_smoke(monkeypatch):
    # Require backend URLs
    meili = os.getenv("MEILI_URL")
    qdrant = os.getenv("QDRANT_URL")
    if not (meili and qdrant):
        pytest.skip("MEILI_URL/QDRANT_URL not set")

    # Make local imports work like the CLI smokes
    sys.path.insert(0, os.getcwd())

    # Run the script and assert zero exit code
    import subprocess

    proc = subprocess.run([
        sys.executable,
        "scripts/smoke_retrieval_tenants.py",
    ])
    assert proc.returncode == 0, "tenant retrieval smoke failed"
