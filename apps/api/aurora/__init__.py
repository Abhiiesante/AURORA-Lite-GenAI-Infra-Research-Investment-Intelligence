"""
AURORA-Lite API package.
Phase 2 — M1 scaffolding for Research Copilot v2.

This package can be imported as either `aurora` or `apps.api.aurora` in tests.
To ensure singletons (like `config.settings`) stay consistent across both
import paths, we alias submodules into sys.modules under both names.
"""

# Lightweight re-exports used by tests
from . import retrieval  # noqa: F401

# Ensure config module is a singleton across both import paths
import sys as _sys
from . import config as _config  # noqa: F401

# Alias so that importing apps.api.aurora.config returns the same module object
if _config is not None:
	_sys.modules.setdefault("apps.api.aurora.config", _config)

# Optionally, also expose this package under the apps.api.aurora namespace if needed
mod = _sys.modules.get(__name__)
if mod is not None:
	_sys.modules.setdefault("apps.api.aurora", mod)

