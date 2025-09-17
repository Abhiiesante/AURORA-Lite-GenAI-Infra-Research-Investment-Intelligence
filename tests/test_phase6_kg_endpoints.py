from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from apps.api.aurora.main import app
from apps.api.aurora.db import get_session


def _now():
    return datetime.now(timezone.utc).isoformat()


def _seed_nodes_and_edges():
    now = _now()
    with get_session() as s:
        # Seed three companies for /kg/find
        s.exec(
            """
            INSERT OR IGNORE INTO kg_nodes (tenant_id, uid, type, properties_json, valid_from, valid_to, provenance_id, created_at)
            VALUES
            (NULL, 'company:test-a', 'Company', '{"name":"Aco","segment":"vector-db"}', :vf, NULL, NULL, :now),
            (NULL, 'company:test-b', 'Company', '{"name":"Bco","segment":"vector-db"}', :vf, NULL, NULL, :now),
            (NULL, 'company:test-c', 'Company', '{"name":"Cco","segment":"mlops"}', :vf, NULL, NULL, :now)
            """,
            {"vf": now, "now": now},
        )
        # Seed two nodes and two edges for /kg/edges
        s.exec(
            """
            INSERT OR IGNORE INTO kg_nodes (tenant_id, uid, type, properties_json, valid_from, valid_to, provenance_id, created_at)
            VALUES
            (NULL, 'company:e2e', 'Company', '{"name":"E2E"}', :vf, NULL, NULL, :now)
            """,
            {"vf": now, "now": now},
        )
        s.exec(
            """
            INSERT OR IGNORE INTO kg_nodes (tenant_id, uid, type, properties_json, valid_from, valid_to, provenance_id, created_at)
            VALUES
            (NULL, 'person:e2e', 'Person', '{"name":"Jane"}', :vf, NULL, NULL, :now)
            """,
            {"vf": now, "now": now},
        )
        s.exec(
            """
            INSERT INTO kg_edges (tenant_id, src_uid, dst_uid, type, properties_json, valid_from, valid_to, provenance_id, created_at)
            VALUES
            (NULL, 'company:e2e', 'person:e2e', 'EMPLOYS', '{"role":"Eng"}', :vf, NULL, NULL, :now),
            (NULL, 'person:e2e', 'company:e2e', 'WORKS_AT', '{"role":"Eng"}', :vf, NULL, NULL, :now)
            """,
            {"vf": now, "now": now},
        )
        s.commit()


def test_find_pagination_and_filters():
    _seed_nodes_and_edges()
    with TestClient(app) as client:
        now = _now()
        # Filter by type + uid_prefix + prop_contains
        r1 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&prop_contains=vector-db&as_of={now}&limit=1&offset=0")
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get("limit") == 1
        # next page
        if d1.get("next_offset") is not None:
            r2 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&prop_contains=vector-db&as_of={now}&limit=1&offset={d1['next_offset']}")
            assert r2.status_code == 200

        # JSON-like filter: prop_key/prop_value eq
        r3 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&prop_key=segment&prop_value=mlops&prop_op=eq&as_of={now}")
        assert r3.status_code == 200
        d3 = r3.json()
        uids = {n.get('uid') for n in d3.get('nodes', [])}
        # Should include only test-c
        assert 'company:test-c' in uids

        # Cursor-based pagination: fetch first page then use next_cursor
        r4 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&prop_contains=vector-db&as_of={now}&limit=1")
        assert r4.status_code == 200
        d4 = r4.json()
        cur = d4.get('next_cursor')
        if cur:
            r5 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&prop_contains=vector-db&as_of={now}&limit=1&cursor={cur}")
            assert r5.status_code == 200


def test_edges_pagination_and_direction():
    _seed_nodes_and_edges()
    with TestClient(app) as client:
        now = _now()
        # all directions
        r_all = client.get(f"/kg/edges?uid=company:e2e&as_of={now}&direction=all&limit=1&offset=0")
        assert r_all.status_code == 200
        d_all = r_all.json()
        assert d_all.get("limit") == 1
        # outgoing
        r_out = client.get(f"/kg/edges?uid=company:e2e&as_of={now}&direction=out")
        assert r_out.status_code == 200
        # incoming
        r_in = client.get(f"/kg/edges?uid=company:e2e&as_of={now}&direction=in")
        assert r_in.status_code == 200

        # Cursor-based pagination
        r0 = client.get(f"/kg/edges?uid=company:e2e&as_of={now}&direction=all&limit=1")
        assert r0.status_code == 200
        d0 = r0.json()
        cur = d0.get('next_cursor')
        if cur:
            r1 = client.get(f"/kg/edges?uid=company:e2e&as_of={now}&direction=all&limit=1&cursor={cur}")
            assert r1.status_code == 200


def test_find_empty_and_malformed_cursor():
    _seed_nodes_and_edges()
    with TestClient(app) as client:
        now = _now()
        # Empty results: filter that matches nothing
        r = client.get(f"/kg/find?type=Company&uid_prefix=zzz:&as_of={now}&limit=5")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("nodes"), list)
        assert d.get("nodes") == []
        assert d.get("next_offset") is None
        assert d.get("next_cursor") is None

        # Large page: request a big limit larger than available
        r2 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&as_of={now}&limit=1000")
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("limit") == 1000
        # We seeded only a few; no next cursors expected
        assert d2.get("next_offset") in (None, 0)
        assert d2.get("next_cursor") in (None, '')

        # Malformed cursor: should gracefully ignore and treat as offset path
        bad = "not-a-base64-cursor"
        r3 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&as_of={now}&limit=1&cursor={bad}")
        assert r3.status_code == 200


def test_find_cursor_termination():
    _seed_nodes_and_edges()
    with TestClient(app) as client:
        now = _now()
        # Two-page traversal, third page should not have a next_cursor
        r1 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&prop_contains=vector-db&as_of={now}&limit=1")
        assert r1.status_code == 200
        d1 = r1.json()
        cur1 = d1.get("next_cursor")
        assert cur1 is not None  # there should be at least 2 vector-db entries
        r2 = client.get(f"/kg/find?type=Company&uid_prefix=company:test&prop_contains=vector-db&as_of={now}&limit=1&cursor={cur1}")
        assert r2.status_code == 200
        d2 = r2.json()
        # After consuming the second item, there should be no further cursor
        assert d2.get("next_cursor") in (None, '')


def test_edges_empty_large_page_and_malformed_cursor():
    _seed_nodes_and_edges()
    with TestClient(app) as client:
        now = _now()
        # Empty results for unknown uid
        r = client.get(f"/kg/edges?uid=company:unknown&as_of={now}&direction=all&limit=10")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("edges"), list)
        assert d.get("edges") == []
        assert d.get("next_offset") is None
        assert d.get("next_cursor") is None

        # Large page should not produce next cursor when fewer rows exist
        r2 = client.get(f"/kg/edges?uid=company:e2e&as_of={now}&direction=all&limit=1000")
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("limit") == 1000
        assert d2.get("next_cursor") in (None, '')

        # Malformed cursor should not error
        bad = "@@@@"
        r3 = client.get(f"/kg/edges?uid=company:e2e&as_of={now}&direction=all&limit=1&cursor={bad}")
        assert r3.status_code == 200