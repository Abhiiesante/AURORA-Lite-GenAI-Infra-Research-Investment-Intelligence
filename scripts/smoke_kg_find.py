from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

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
        headers = {"x-dev-token": tok} if tok else {}

        # Seed a node if admin available
        resp = client.post(
            "/admin/kg/nodes/upsert",
            json={
                "uid": "company:find-smoke",
                "type": "Company",
                "props": {"name": "FindCo", "segment": "vector-db"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        if resp.status_code == 404:
            print("admin unavailable; skipping find smoke")
            return 0
        if resp.status_code not in (200, 201):
            print("ERROR: upsert failed", resp.status_code, resp.text)
            return 1

        # Query with filters (use params to ensure proper URL encoding)
        r = client.get(
            "/kg/find",
            params={
                "type": "Company",
                "uid_prefix": "company:find",
                "prop_contains": "vector-db",
                "as_of": now,
                "limit": 5,
            },
        )
        print("GET /kg/find ->", r.status_code)
        if r.status_code != 200:
            print("ERROR: find failed", r.status_code, r.text)
            return 1
        data = r.json()
        nodes = data.get("nodes") or []
        if not any(n.get("uid") == "company:find-smoke" for n in nodes):
            print("ERROR: find did not return expected node", nodes)
            return 1
        # Check pagination fields
        if "offset" not in data or "limit" not in data:
            print("ERROR: pagination fields missing in /kg/find response", data)
            return 1
        # Insert another node to exercise offset
        resp2 = client.post(
            "/admin/kg/nodes/upsert",
            json={
                "uid": "company:find-smoke2",
                "type": "Company",
                "props": {"name": "FindCo2", "segment": "vector-db"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        if resp2.status_code in (200, 201):
            # First page limit=1 should have next_offset=1
            r2a = client.get(
                "/kg/find",
                params={
                    "type": "Company",
                    "uid_prefix": "company:find",
                    "prop_contains": "vector-db",
                    "as_of": now,
                    "limit": 1,
                    "offset": 0,
                },
            )
            if r2a.status_code == 200:
                d2a = r2a.json()
                if d2a.get("next_offset") != 1:
                    print("ERROR: expected next_offset=1 for first /kg/find page, got", d2a.get("next_offset"))
                    return 1
                # Also try cursor-based next page if provided
                if d2a.get("next_cursor"):
                    cur = d2a["next_cursor"]
                    rc = client.get(
                        "/kg/find",
                        params={
                            "type": "Company",
                            "uid_prefix": "company:find",
                            "prop_contains": "vector-db",
                            "as_of": now,
                            "limit": 1,
                            "cursor": cur,
                        },
                    )
                    if rc.status_code != 200:
                        print("ERROR: cursor page for /kg/find failed", rc.status_code, rc.text)
                        return 1
            # Second page limit=1 should likely be last; next_offset may be None if only two results
            r2b = client.get(
                "/kg/find",
                params={
                    "type": "Company",
                    "uid_prefix": "company:find",
                    "prop_contains": "vector-db",
                    "as_of": now,
                    "limit": 1,
                    "offset": 1,
                },
            )
            if r2b.status_code == 200:
                d2b = r2b.json()
                # next_offset may be None or 2 if more items exist; ensure we have at least one node
                nodes2 = d2b.get("nodes") or []
                if len(nodes2) < 1:
                    print("ERROR: expected at least one node in paged /kg/find", nodes2)
                    return 1
            else:
                print("WARN: paged /kg/find returned", r2b.status_code)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
