"""LakeFS integration abstraction (Phase 6 scaffold).

This module provides a placeholder interface for obtaining a canonical snapshot hash
from a LakeFS commit (future implementation). For now it falls back to local SHA256
computation of a provided payload to preserve deterministic behavior.

Pluggable design:
- get_current_commit(): fetch active LakeFS branch + commit id (stub)
- compute_snapshot_hash(payload_dict): returns a sha256 over canonical JSON encoding

Future enhancements:
- Replace stub with real LakeFS API client calls (auth, branch, commit metadata)
- Optionally embed LakeFS commit id into KGSnapshot rows
"""
from __future__ import annotations

from typing import Any, Dict, Optional
import json, hashlib


def get_current_commit(branch: Optional[str] = None) -> Optional[str]:
    """Return the latest LakeFS commit id for a branch (stub).

    Currently returns None to indicate no external commit id is available.
    """
    return None


def compute_snapshot_hash(payload: Dict[str, Any]) -> str:
    """Compute canonical sha256 over JSON payload.

    Deterministic, stable ordering via sort_keys + compact separators.
    """
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()  # nosec


__all__ = ["get_current_commit", "compute_snapshot_hash"]
