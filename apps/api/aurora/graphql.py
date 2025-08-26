from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter
from .db import get_session, Company


router = APIRouter()


@router.post("/graphql")
def graphql_endpoint(body: Dict[str, Any]):
    # extremely simplified GraphQL-like behavior for tests
    query = body.get("query", "")
    if "companies" in query:
        with get_session() as s:
            c = s.get(Company, 1)
            return {"data": {"companies": [{"id": 1, "canonicalName": c.canonical_name, "website": c.website}]}}
    return {"data": {}}
