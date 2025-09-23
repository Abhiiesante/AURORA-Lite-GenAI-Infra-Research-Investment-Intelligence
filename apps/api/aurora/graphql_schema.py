"""GraphQL schema (Phase 6 scaffold) using Strawberry if available.

This is an optional dependency; runtime will degrade gracefully if strawberry
is not installed. To enable, add `strawberry-graphql` to requirements and
mount the router within FastAPI app startup.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any

try:
    import strawberry  # type: ignore
except Exception:  # pragma: no cover - strawberry optional
    strawberry = None  # type: ignore

if strawberry:
    @strawberry.type
    class Edge:
        src: str
        dst: str
        type: str
        props: Optional[str]

    @strawberry.type
    class Node:
        uid: str
        type: str
        props: Optional[str]

    @strawberry.type
    class NodeResult:
        as_of: str
        node: Optional[Node]
        neighbors: List[Node]
        edges: List[Edge]

    def _fetch_node_bundle(node_id: str, as_of: Optional[str], depth: int) -> Dict[str, Any]:
        # Re-use existing REST logic by invoking kg_get_node directly.
        # We create a synthetic request object with minimal attributes.
        from fastapi import Request  # type: ignore
        from starlette.datastructures import Headers  # type: ignore
        from .main import kg_get_node  # type: ignore
        class _Dummy:
            def __init__(self):
                self.state = type("S", (), {})()
        dummy = _Dummy()
        # Provide a fake request (FastAPI will not inspect further for simple usage)
        result = kg_get_node(node_id=node_id, request=dummy, as_of=as_of, depth=depth, limit=200)
        return result

    @strawberry.type
    class Query:
        @strawberry.field
        def node(self, id: str, as_of: Optional[str] = None, depth: int = 1) -> NodeResult:  # type: ignore
            data = _fetch_node_bundle(id, as_of, depth)
            node = data.get("node") or {}
            neighbors = data.get("neighbors") or []
            edges = data.get("edges") or []
            return NodeResult(
                as_of=data.get("as_of"),
                node=Node(uid=node.get("uid"), type=node.get("type"), props=node.get("props")) if node else None,
                neighbors=[Node(uid=n.get("uid"), type=n.get("type"), props=n.get("props")) for n in neighbors],
                edges=[Edge(src=e.get("src"), dst=e.get("dst"), type=e.get("type"), props=e.get("props")) for e in edges],
            )

    schema = strawberry.Schema(query=Query)  # type: ignore
else:  # pragma: no cover
    schema = None  # type: ignore

__all__ = ["schema"]
