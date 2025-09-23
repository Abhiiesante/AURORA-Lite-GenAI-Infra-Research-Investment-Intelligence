#!/usr/bin/env bash
set -euo pipefail

# Lightweight prestart hook for API container.
# Intentionally minimal: perform quick import check and print versions.
python - <<'PY'
import sys
import platform
try:
    import aurora
    mod = getattr(aurora, '__name__', 'aurora')
except Exception as e:
    mod = f"import-error: {e}"
print({
    'python': sys.version.split()[0],
    'platform': platform.platform(),
    'module': mod,
})
PY

echo "[prestart] OK"
