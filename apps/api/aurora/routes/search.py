from fastapi import APIRouter, Query
from typing import List
from ..clients import meili

router = APIRouter()


@router.get("/")
def search(q: str = Query(..., description="Query string"), limit: int = 10):
    try:
        idx = meili.index("companies")
        res = idx.search(q, {"limit": limit})
        return {"query": q, "hits": res.get("hits", []), "estimatedTotalHits": res.get("estimatedTotalHits")}
    except Exception:
        return {"query": q, "hits": [], "estimatedTotalHits": 0}
