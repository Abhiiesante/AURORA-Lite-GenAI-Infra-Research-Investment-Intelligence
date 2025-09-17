from fastapi import APIRouter
from ..db import init_db, Company, get_session
from ..clients import meili, qdrant
from ..rag_service import seed_sample_docs
from sqlmodel import select

router = APIRouter()

# Align with include_router(prefix="/health"): GET /health
@router.get("/")
def health():
    return {"status": "ok"}


# Will be exposed at POST /health/seed via router prefix
@router.post("/seed")
def seed():
    init_db()
    with get_session() as s:
        col = getattr(Company, "canonical_name")  # type: ignore[attr-defined]
        rows = list(s.exec(select(Company).where(col == "ExampleAI")))
        exists = rows[0] if rows else None
        if not exists:
            s.add(Company(canonical_name="ExampleAI", website="https://example.ai", segments="vector_db", hq_country="US"))
            s.commit()
    # seed meilisearch index
    try:
        if meili:
            meili.index("companies").add_documents([
                {"id": 1, "canonical_name": "ExampleAI", "segments": ["vector_db"], "website": "https://example.ai"}
            ])
    except Exception:
        pass
    # seed qdrant collection (empty schema is fine; vectors added later)
    try:
        if qdrant:
            qdrant.get_collection("docs")
    except Exception:
        try:
            if qdrant:
                from qdrant_client.models import Distance, VectorParams
                qdrant.create_collection(
                    collection_name="docs",
                    vectors_config={
                        "text": VectorParams(size=384, distance=Distance.COSINE)
                    }
                )
        except Exception:
            pass
    return {"status": "seeded"}


# Will be exposed at POST /health/seed-rag via router prefix
@router.post("/seed-rag")
def seed_rag():
    return seed_sample_docs()
