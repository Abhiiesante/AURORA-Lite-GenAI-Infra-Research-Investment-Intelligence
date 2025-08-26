from fastapi import APIRouter, Response
import csv
from io import StringIO
from sqlmodel import select
from ..db import get_session, Company

router = APIRouter()


@router.get("/companies.csv")
def companies_csv():
    with get_session() as s:
        rows = list(s.exec(select(Company)))
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "canonical_name", "website", "hq_country", "segments", "funding_total"])
    for r in rows:
        writer.writerow([r.id, r.canonical_name, r.website or "", r.hq_country or "", r.segments or "", r.funding_total or ""])
    return Response(content=buf.getvalue(), media_type="text/csv")
