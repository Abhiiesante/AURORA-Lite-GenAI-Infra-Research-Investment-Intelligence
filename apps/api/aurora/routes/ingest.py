from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from ..etl import upsert_companies_from_items

router = APIRouter()


class Items(BaseModel):
    items: List[Dict]


@router.post("/companies")
def ingest_companies(payload: Items):
    count = upsert_companies_from_items(payload.items)
    return {"ingested": count}
