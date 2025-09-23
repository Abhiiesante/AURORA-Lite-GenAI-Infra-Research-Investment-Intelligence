import os
import json
from typing import Any, Mapping, Sequence, cast
try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - editor convenience
    pd = None  # type: ignore
try:  # Optional deps; script can run partially without them
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - editor convenience
    SentenceTransformer = None  # type: ignore[assignment]
try:
    from qdrant_client import QdrantClient  # type: ignore[import-not-found]
    from qdrant_client.models import Distance, VectorParams  # type: ignore[import-not-found]
    from qdrant_client.http.models import Batch, ExtendedPointId, Payload  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    QdrantClient = None  # type: ignore[assignment]
    Distance = None  # type: ignore[assignment]
    VectorParams = None  # type: ignore[assignment]
    Batch = None  # type: ignore[assignment]
    ExtendedPointId = None  # type: ignore[assignment]
    Payload = None  # type: ignore[assignment]
try:
    import meilisearch  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    meilisearch = None  # type: ignore[assignment]

MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
AURORA_DEFAULT_TENANT_ID = os.getenv("AURORA_DEFAULT_TENANT_ID", "1")
TENANT_INDEXING_MODE = os.getenv("TENANT_INDEXING_MODE", "filter").strip().lower()

NEWS_PARQUET = os.getenv("NEWS_PARQUET", "data/raw/news_items.parquet")
NEWS_INDEX = os.getenv("NEWS_INDEX", "news_index")
BASE_VEC_COLLECTION = os.getenv("NEWS_VEC_COLLECTION", "news_chunks")

def _vec_collection_name() -> str:
    if TENANT_INDEXING_MODE == "collection" and AURORA_DEFAULT_TENANT_ID:
        return f"{BASE_VEC_COLLECTION}_tenant_{AURORA_DEFAULT_TENANT_ID}"
    return BASE_VEC_COLLECTION


def main():
    if pd is None:
        print("pandas is not installed. Install with 'pip install pandas pyarrow' to run this script.")
        return
    if not os.path.exists(NEWS_PARQUET):
        print(f"Missing {NEWS_PARQUET}")
        return
    df = pd.read_parquet(NEWS_PARQUET)
    # Index metadata to Meili (optional)
    if meilisearch is None:
        print("meilisearch not installed; skipping metadata indexing. pip install meilisearch to enable.")
    else:
        meili = meilisearch.Client(MEILI_URL)
        try:
            meili.create_index(NEWS_INDEX, {"primaryKey": "url"})
        except Exception:
            pass
        docs = df[["url", "title", "published_at"]].to_dict(orient="records")
        # inject tenant_id for multi-tenancy filtering
        for d in docs:
            d["tenant_id"] = AURORA_DEFAULT_TENANT_ID
        # Ensure Mapping[str, Any] for type checkers with str keys
        docs_for_meili: Sequence[Mapping[str, Any]] = [
            {str(k): v for k, v in cast(dict[Any, Any], d).items()}
            for d in docs
        ]
        idx = meili.index(NEWS_INDEX)
        try:
            # ensure tenant_id is filterable
            idx.update_settings({"filterableAttributes": ["tenant_id"]})
        except Exception:
            pass
        idx.add_documents(docs_for_meili)
    # Vectorize text and push to Qdrant
    # Vectorize text and push to Qdrant (optional)
    if SentenceTransformer is None or QdrantClient is None or VectorParams is None or Distance is None:
        print("sentence-transformers/qdrant_client not installed; skipping vector indexing. pip install 'sentence-transformers qdrant-client' to enable.")
    else:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        texts = (df["clean_text"].fillna("").astype(str)).tolist()
        vecs = model.encode(texts, normalize_embeddings=True)
        client = QdrantClient(url=QDRANT_URL)
        vec_collection = _vec_collection_name()
        try:
            client.get_collection(vec_collection)
        except Exception:
            client.recreate_collection(vec_collection, vectors_config=VectorParams(size=len(vecs[0]), distance=Distance.COSINE))
        ids: list[ExtendedPointId] = [int(i) for i in range(len(df))]  # type: ignore[valid-type]
        vectors: list[list[float]] = [list(map(float, vecs[i].tolist())) for i in range(len(df))]
        payloads: list[Payload] = [  # type: ignore[valid-type]
            {
                "url": str(df.iloc[i]["url"]),
                "title": str(df.iloc[i]["title"]),
                "tenant_id": AURORA_DEFAULT_TENANT_ID,
            }
            for i in range(len(df))
        ]
        batch = Batch(ids=ids, vectors=vectors, payloads=payloads)  # type: ignore[call-arg]
        client.upsert(vec_collection, points=batch)
        print("Indexed", len(ids))


if __name__ == "__main__":
    main()
