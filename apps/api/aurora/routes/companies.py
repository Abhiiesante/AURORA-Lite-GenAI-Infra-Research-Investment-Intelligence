from fastapi import APIRouter, HTTPException
from typing import List, Optional
from sqlmodel import select
from pydantic import BaseModel
from ..db import Company, get_session
from ..clients import meili

router = APIRouter()


@router.get("/", response_model=List[Company])
def list_companies():
    with get_session() as s:
        return list(s.exec(select(Company)))


class CompanyCreate(BaseModel):
    canonical_name: str
    website: Optional[str] = None
    hq_country: Optional[str] = None
    segments: Optional[List[str]] = None
    funding_total: Optional[float] = None


@router.post("/", response_model=Company)
def upsert_company(payload: CompanyCreate):
    with get_session() as s:
        col = getattr(Company, "canonical_name")  # type: ignore[attr-defined]
        rows = list(s.exec(select(Company).where(col == payload.canonical_name)))
        existing = rows[0] if rows else None
        if existing:
            existing.website = payload.website or existing.website
            existing.hq_country = payload.hq_country or existing.hq_country
            if payload.segments is not None:
                existing.segments = ",".join(payload.segments)
            if payload.funding_total is not None:
                existing.funding_total = payload.funding_total
            s.add(existing)
            s.commit()
            s.refresh(existing)
            doc = {
                "id": existing.id,
                "canonical_name": existing.canonical_name,
                "segments": (existing.segments or "").split(",") if existing.segments else [],
                "website": existing.website,
            }
            try:
                if meili:
                    meili.index("companies").add_documents([doc])
            except Exception:
                pass
            return existing
        else:
            comp = Company(
                canonical_name=payload.canonical_name,
                website=payload.website,
                hq_country=payload.hq_country,
                segments=",".join(payload.segments) if payload.segments else None,
                funding_total=payload.funding_total,
            )
            s.add(comp)
            s.commit()
            s.refresh(comp)
            doc = {
                "id": comp.id,
                "canonical_name": comp.canonical_name,
                "segments": payload.segments or [],
                "website": comp.website,
            }
            try:
                if meili:
                    meili.index("companies").add_documents([doc])
            except Exception:
                pass
            return comp


@router.get("/{company_id}", response_model=Company)
def get_company(company_id: int):
    with get_session() as s:
        obj = s.get(Company, company_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Company not found")
        return obj
