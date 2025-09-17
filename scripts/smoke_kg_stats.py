from __future__ import annotations

import sys
import os
from fastapi.testclient import TestClient

# Ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from apps.api.aurora.main import app  # noqa: E402


def main() -> int:
    with TestClient(app) as client:
        r = client.get("/kg/stats")
        if r.status_code != 200:
            print("ERROR: /kg/stats failed", r.status_code, r.text)
            return 1
        data = r.json()
        for k in ["nodes_total", "edges_total", "latest_node_created_at", "latest_edge_created_at"]:
            if k not in data:
                print("ERROR: missing key in stats:", k, data)
                return 1
        print("stats:", data)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
