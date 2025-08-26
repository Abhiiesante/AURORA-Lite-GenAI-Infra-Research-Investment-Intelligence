from pydantic import BaseModel, Field
from typing import List, Dict


class SWOT(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class Thesis(BaseModel):
    statement: str = ""
    evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class CompanyBrief(BaseModel):
    company: str
    summary: str
    swot: SWOT
    five_forces: Dict[str, str] = Field(default_factory=dict)
    theses: List[Thesis] = Field(default_factory=list)
    # Require at least one source when enforcing citations
    sources: List[str] = Field(default_factory=list)
