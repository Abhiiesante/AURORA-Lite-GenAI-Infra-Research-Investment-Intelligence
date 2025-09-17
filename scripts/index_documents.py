from __future__ import annotations

r"""
Populate Meilisearch and Qdrant with a small sample corpus to exercise the hybrid path.
This script is idempotent and safe to run when either backend is unavailable.

Usage (PowerShell):
    ..\\.venv\\Scripts\\python scripts\\index_documents.py
"""

from typing import Any, Dict, List

from apps.api.aurora.clients import meili, qdrant
import os

TENANT_ID = os.getenv("AURORA_DEFAULT_TENANT_ID", "1")
TENANT_INDEXING_MODE = (os.getenv("VECTOR_TENANT_MODE") or os.getenv("TENANT_INDEXING_MODE") or "filter").strip().lower()
BASE_COLLECTION = os.getenv("DOCUMENTS_VEC_COLLECTION_BASE", "documents")

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
        # Optional: reset index
        if (os.getenv("RESET_MEILI") or "").strip().lower() in ("1", "true", "yes"):
            try:
                meili.delete_index("documents")
                print("[meili] deleted index 'documents'")
            except Exception:
                pass
            idx = meili.index("documents")
        # Set primary key if not exists; Meili will upsert by id
        try:
            meili.create_index("documents", {"primaryKey": "id"})
            print("[meili] created index 'documents'")
        except Exception:
            pass
        # Ensure tenant_id filterable
        try:
            idx.update_settings({"filterableAttributes": ["tenant_id"]})
        except Exception:
            pass
        # Use per-tenant IDs to prevent overwriting between tenants
        docs = [
            {
                **d,
                "id": f"{TENANT_ID}-{d['id']}",
                "tenant_id": TENANT_ID,
            }
            for d in DOCS
        ]
        res = idx.add_documents(docs)
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
        dim = int(embedder.get_sentence_embedding_dimension() or 384)
    except Exception:
        print("[qdrant] sentence-transformers not available; skipping")
        return

    try:
        from qdrant_client.models import Distance, VectorParams, Batch, ExtendedPointId  # type: ignore
        import uuid

        base = BASE_COLLECTION
        collection_name = f"{base}_tenant_{TENANT_ID}" if TENANT_INDEXING_MODE == "collection" else base
        # Optional: reset qdrant data
        reset_qdrant = (os.getenv("RESET_QDRANT") or "").strip().lower() in ("1", "true", "yes")
        reset_all = (os.getenv("RESET_QDRANT_ALL") or "").strip().lower() in ("1", "true", "yes")
        if reset_all:
            try:
                qdrant.delete_collection(collection_name=base)
                print(f"[qdrant] deleted collection '{base}'")
            except Exception:
                pass
        elif reset_qdrant:
            try:
                if TENANT_INDEXING_MODE == "collection":
                    qdrant.delete_collection(collection_name=collection_name)
                    print(f"[qdrant] deleted per-tenant collection '{collection_name}'")
                else:
                    # Filter mode: delete only current tenant's points
                    from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore
                    qdrant.delete(
                        collection_name=collection_name,
                        points_selector=None,
                        query_filter=Filter(must=[FieldCondition(key="tenant_id", match=MatchValue(value=TENANT_ID))]),
                    )
                    print(f"[qdrant] deleted points for tenant '{TENANT_ID}' in '{collection_name}'")
            except Exception:
                pass
        collections = qdrant.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            print(f"[qdrant] created collection '{collection_name}'")

        vectors = embedder.encode([d["text"] for d in DOCS])
        # Use deterministic UUIDs per tenant+doc id to satisfy Qdrant ID constraints
        ids: List[ExtendedPointId] = [
            str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{TENANT_ID}-{d['id']}")) for d in DOCS
        ]
        vecs = [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]
        payloads = []
        for d in DOCS:
            tags = list(d.get("tags", [])) + [f"tenant:{TENANT_ID}"]
            payloads.append({**d, "tenant_id": TENANT_ID, "tags": tags})
        batch = Batch(ids=ids, vectors=vecs, payloads=payloads)
        qdrant.upsert(collection_name=collection_name, points=batch)
        print(f"[qdrant] upserted {len(ids)} points")
    except Exception as e:
        print(f"[qdrant] indexing failed: {e}")


if __name__ == "__main__":
    index_meilisearch()
    index_qdrant()
