from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient

# Ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from apps.api.aurora.main import app  # noqa: E402


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    with TestClient(app) as client:
        tok = os.environ.get("DEV_ADMIN_TOKEN")
        no_admin = os.environ.get("SMOKE_NO_ADMIN") == "1"
        headers = {"x-dev-token": tok} if (tok and not no_admin) else {}

        # Try to upsert a test node; if admin is unavailable (404), skip gracefully
        if not no_admin:
            resp = client.post(
                "/admin/kg/nodes/upsert",
                json={
                    "uid": "company:smoke",
                    "type": "Company",
                    "props": {"name": "SmokeCo"},
                    "valid_from": now,
                    "close_open": True,
                    "provenance": {"pipeline_version": "smoke-v1"},
                },
                headers=headers,
            )
            if resp.status_code == 404:
                print("admin unavailable; skipping seed step and smoke")
                return 0
            if resp.status_code not in (200, 201):
                print("ERROR: upsert failed", resp.status_code, resp.text)
                return 1
        else:
            # No-admin mode: don't attempt seeding; only perform read checks if desired in future
            print("no-admin mode: skipping admin seed; exiting successfully")
            return 0

        # Fetch time-travel node view
        r2 = client.get(f"/kg/node/company:smoke?as_of={now}&depth=1")
        print("GET /kg/node/company:smoke ->", r2.status_code)
        if r2.status_code != 200:
            print("ERROR: node fetch failed", r2.status_code, r2.text)
            return 1
        data: dict[str, Any] = r2.json()
        node = data.get("node") or {}
        if not node or node.get("uid") != "company:smoke":
            print("ERROR: missing or wrong node in response", node)
            return 1
        print("OK: node fetched with", len(data.get("neighbors", [])), "neighbors and", len(data.get("edges", [])), "edges")

        # Batch endpoint (single id)
        r3 = client.get(f"/kg/nodes?ids=company:smoke&as_of={now}")
        print("GET /kg/nodes ->", r3.status_code)
        if r3.status_code != 200:
            print("ERROR: batch fetch failed", r3.status_code, r3.text)
            return 1
        data2 = r3.json()
        nodes = data2.get("nodes") or []
        if not any(n.get("uid") == "company:smoke" for n in nodes):
            print("ERROR: batch response missing company:smoke", nodes)
            return 1
        # Pagination params should be present
        if "offset" not in data2 or "limit" not in data2:
            print("ERROR: pagination fields missing in /kg/nodes response", data2)
            return 1
        # Create more nodes to test pagination window on ids and next_offset
        resp2 = client.post(
            "/admin/kg/nodes/upsert",
            json={
                "uid": "company:smoke2",
                "type": "Company",
                "props": {"name": "SmokeCo2"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        resp3 = client.post(
            "/admin/kg/nodes/upsert",
            json={
                "uid": "company:smoke3",
                "type": "Company",
                "props": {"name": "SmokeCo3"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        if resp2.status_code in (200, 201) and resp3.status_code in (200, 201):
            # ids pagination over 3 ids with limit=1: expect next_offset to advance 0->1->2 and then None
            base_ids = "company:smoke,company:smoke2,company:smoke3"
            r4 = client.get(f"/kg/nodes?ids={base_ids}&as_of={now}&offset=0&limit=1")
            if r4.status_code == 200:
                d4 = r4.json()
                if d4.get("next_offset") != 1:
                    print("ERROR: expected next_offset=1 at first page, got", d4.get("next_offset"))
                    return 1
            r5 = client.get(f"/kg/nodes?ids={base_ids}&as_of={now}&offset=1&limit=1")
            if r5.status_code == 200:
                d5 = r5.json()
                if d5.get("next_offset") != 2:
                    print("ERROR: expected next_offset=2 at second page, got", d5.get("next_offset"))
                    return 1
            r6 = client.get(f"/kg/nodes?ids={base_ids}&as_of={now}&offset=2&limit=1")
            if r6.status_code == 200:
                d6 = r6.json()
                if d6.get("next_offset") is not None:
                    print("ERROR: expected next_offset=None at last page, got", d6.get("next_offset"))
                    return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
