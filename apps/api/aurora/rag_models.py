from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    source: str = Field(..., description="URL or doc id")
    snippet: str = Field(..., description="Quoted text or summary used")


class MicroThesis(BaseModel):
    statement: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Evidence]

    @field_validator("evidence")
    @classmethod
    def non_empty_evidence(cls, v: List[Evidence]):
        if not v:
            raise ValueError("evidence must be non-empty")
        return v


class FiveForces(BaseModel):
    rivalry: str
    new_entrants: str
    supplier_power: str
    buyer_power: str
    substitutes: str


class CompanyBrief(BaseModel):
    company: str
    summary: str
    five_forces: FiveForces
    theses: List[MicroThesis]

    @field_validator("theses")
    @classmethod
    def non_empty_theses(cls, v: List[MicroThesis]):
        if not v:
            raise ValueError("theses must be non-empty")
        return v


class ComparisonRow(BaseModel):
    metric: str
    a: str | float | int
    b: str | float | int
    delta: str | float | int


class ComparativeAnswer(BaseModel):
    answer: str
    comparisons: List[ComparisonRow] = Field(default_factory=list)
    top_risks: List[dict] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class CoercionResult(BaseModel):
    ok: bool
    error: Optional[str] = None
    data: Optional[CompanyBrief] = None


def coerce_company_brief_json(obj: dict) -> CoercionResult:
    try:
        brief = CompanyBrief.model_validate(obj)
        # Reject if any evidence sources are empty strings
        for t in brief.theses:
            for e in t.evidence:
                if not e.source.strip():
                    raise ValueError("empty evidence source")
        return CoercionResult(ok=True, data=brief)
    except Exception as e:  # noqa: BLE001
        return CoercionResult(ok=False, error=str(e))
