from fastapi import APIRouter
from ..db import init_db, Company, get_session
from ..clients import meili, qdrant
from ..rag_service import seed_sample_docs
from sqlmodel import select

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/seed")
def seed():
    init_db()
    with get_session() as s:
        exists = s.exec(select(Company).where(Company.canonical_name == "ExampleAI")).first()
        if not exists:
            s.add(Company(canonical_name="ExampleAI", website="https://example.ai", segments="vector_db", hq_country="US"))
            s.commit()
    # seed meilisearch index
    try:
        meili.index("companies").add_documents([
            {"id": 1, "canonical_name": "ExampleAI", "segments": ["vector_db"], "website": "https://example.ai"}
        ])
    except Exception:
        pass
    # seed qdrant collection (empty schema is fine; vectors added later)
    try:
        qdrant.get_collection("docs")
    except Exception:
        try:
            from qdrant_client.models import Distance, VectorParams, NamedVectors
            qdrant.create_collection(
                collection_name="docs",
                vectors_config=NamedVectors({
                    "text": VectorParams(size=384, distance=Distance.COSINE)
                })
            )
        except Exception:
            pass
    return {"status": "seeded"}


@router.post("/seed-rag")
def seed_rag():
    return seed_sample_docs()
