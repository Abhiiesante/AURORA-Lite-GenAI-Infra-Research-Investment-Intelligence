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

        # Seed two nodes and two edges if admin available
        resp_n1 = client.post(
            "/admin/kg/nodes/upsert",
            json={
                "uid": "company:edge-smoke",
                "type": "Company",
                "props": {"name": "EdgeCo"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        if resp_n1.status_code == 404:
            print("admin unavailable; skipping edges smoke")
            return 0
        if resp_n1.status_code not in (200, 201):
            print("ERROR: node1 upsert failed", resp_n1.status_code, resp_n1.text)
            return 1
        resp_n2 = client.post(
            "/admin/kg/nodes/upsert",
            json={
                "uid": "person:edge-smoke",
                "type": "Person",
                "props": {"name": "Edge Person"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        if resp_n2.status_code not in (200, 201):
            print("ERROR: node2 upsert failed", resp_n2.status_code, resp_n2.text)
            return 1
        # Two edges both directions
        e1 = client.post(
            "/admin/kg/edges/upsert",
            json={
                "src_uid": "company:edge-smoke",
                "dst_uid": "person:edge-smoke",
                "type": "EMPLOYS",
                "props": {"role": "Engineer"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        e2 = client.post(
            "/admin/kg/edges/upsert",
            json={
                "src_uid": "person:edge-smoke",
                "dst_uid": "company:edge-smoke",
                "type": "WORKS_AT",
                "props": {"role": "Engineer"},
                "valid_from": now,
                "close_open": True,
            },
            headers=headers,
        )
        if e1.status_code not in (200, 201) or e2.status_code not in (200, 201):
            print("ERROR: edge upserts failed", e1.status_code, e2.status_code)
            return 1

        # Query edges all directions (use params for proper encoding)
        r_all = client.get(
            "/kg/edges",
            params={
                "uid": "company:edge-smoke",
                "as_of": now,
                "direction": "all",
                "limit": 1,
                "offset": 0,
            },
        )
        if r_all.status_code != 200:
            print("ERROR: /kg/edges all failed", r_all.status_code, r_all.text)
            return 1
        d_all = r_all.json()
        if d_all.get("next_offset") != 1:
            print("ERROR: expected next_offset=1 on first page", d_all)
            return 1
        # Next page
        r_all2 = client.get(
            "/kg/edges",
            params={
                "uid": "company:edge-smoke",
                "as_of": now,
                "direction": "all",
                "limit": 1,
                "offset": 1,
            },
        )
        if r_all2.status_code != 200:
            print("ERROR: /kg/edges all page2 failed", r_all2.status_code, r_all2.text)
            return 1
        # Cursor-based next page if available
        d_all = r_all.json()
        if d_all.get("next_cursor"):
            cur = d_all["next_cursor"]
            r_allc = client.get(
                "/kg/edges",
                params={
                    "uid": "company:edge-smoke",
                    "as_of": now,
                    "direction": "all",
                    "limit": 1,
                    "cursor": cur,
                },
            )
            if r_allc.status_code != 200:
                print("ERROR: /kg/edges cursor page failed", r_allc.status_code, r_allc.text)
                return 1
        # Outgoing only
        r_out = client.get(
            "/kg/edges",
            params={
                "uid": "company:edge-smoke",
                "as_of": now,
                "direction": "out",
            },
        )
        if r_out.status_code != 200:
            print("ERROR: /kg/edges out failed", r_out.status_code, r_out.text)
            return 1
        # Incoming only
        r_in = client.get(
            "/kg/edges",
            params={
                "uid": "company:edge-smoke",
                "as_of": now,
                "direction": "in",
            },
        )
        if r_in.status_code != 200:
            print("ERROR: /kg/edges in failed", r_in.status_code, r_in.text)
            return 1
        print("edges smoke ok")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
