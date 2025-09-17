import os
import sys

from fastapi.testclient import TestClient

# Ensure repo root is on sys.path so 'apps' package resolves when running from scripts/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from apps.api.aurora.main import app


def main() -> int:
    ok = True
    with TestClient(app) as client:
        for path in ["/healthz", "/readyz"]:
            r = client.get(path)
            print(f"GET {path} -> {r.status_code}")
            if r.status_code != 200:
                print(r.text)
                ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
