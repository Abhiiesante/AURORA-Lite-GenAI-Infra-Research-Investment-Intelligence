from __future__ import annotations

"""
Populate Meilisearch and Qdrant with a small sample corpus to exercise the hybrid path.
This script is idempotent and safe to run when either backend is unavailable.

Usage (PowerShell):
  ..\.venv\Scripts\python scripts/index_documents.py
"""

from typing import Any, Dict, List

from apps.api.aurora.clients import meili, qdrant

DOCS: List[Dict[str, Any]] = [
    {
        "id": "doc-1",
        "url": "https://example.com/pinecone-traction",
        "text": "Pinecone reported strong traction with increasing mentions and stars in OSS repos.",
        "tags": ["pinecone", "traction", "stars"],
    },
    {
        "id": "doc-2",
        "url": "https://example.com/weaviate-traction",
        "text": "Weaviate sees consistent commit velocity and active community growth.",
        "tags": ["weaviate", "commits", "community"],
    },
    {
        "id": "doc-3",
        "url": "https://example.com/risks",
        "text": "Competition risk noted across vector DB vendors.",
        "tags": ["risk", "competition"],
    },
]


def index_meilisearch() -> None:
    if not meili:
        print("[meili] client not configured; skipping")
        return
    try:
        idx = meili.index("documents")
        # Set primary key if not exists; Meili will upsert by id
        try:
            meili.create_index("documents", {"primaryKey": "id"})
            print("[meili] created index 'documents'")
        except Exception:
            pass
        res = idx.add_documents(DOCS)
        print(f"[meili] add_documents task: {res}")
    except Exception as e:
        print(f"[meili] indexing failed: {e}")


def index_qdrant() -> None:
    if not qdrant:
        print("[qdrant] client not configured; skipping")
        return
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        dim = embedder.get_sentence_embedding_dimension()
    except Exception:
        print("[qdrant] sentence-transformers not available; skipping")
        return

    try:
        from qdrant_client.models import Distance, VectorParams, PointStruct  # type: ignore

        collections = qdrant.get_collections().collections
        if not any(c.name == "documents" for c in collections):
            qdrant.create_collection(
                collection_name="documents",
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            print("[qdrant] created collection 'documents'")

        vectors = embedder.encode([d["text"] for d in DOCS])
        points = [
            PointStruct(id=i + 1, vector=v.tolist(), payload=doc)  # stable ids for demo
            for i, (doc, v) in enumerate(zip(DOCS, vectors))
        ]
        qdrant.upsert(collection_name="documents", points=points)
        print(f"[qdrant] upserted {len(points)} points")
    except Exception as e:
        print(f"[qdrant] indexing failed: {e}")


if __name__ == "__main__":
    index_meilisearch()
    index_qdrant()
