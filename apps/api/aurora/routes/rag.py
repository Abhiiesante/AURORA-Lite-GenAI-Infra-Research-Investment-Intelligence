from fastapi import APIRouter, Query
from ..rag_service import answer_with_citations

router = APIRouter()

@router.get("/brief")
def generate_brief(company: str = Query(..., description="Company name")):
    qa = answer_with_citations(f"Provide an investor brief with SWOT and risks for {company}. Cite sources.")
    return {"company": company, "brief": qa["answer"], "sources": qa["sources"]}
