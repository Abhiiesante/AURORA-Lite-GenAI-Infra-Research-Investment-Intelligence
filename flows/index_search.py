import os
import json
from typing import Any, Mapping, Sequence, cast
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.http.models import Batch, ExtendedPointId, Payload
import meilisearch

MEILI_URL = os.getenv("MEILI_URL", "http://localhost:7700")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

NEWS_PARQUET = os.getenv("NEWS_PARQUET", "data/raw/news_items.parquet")
NEWS_INDEX = os.getenv("NEWS_INDEX", "news_index")
VEC_COLLECTION = os.getenv("NEWS_VEC_COLLECTION", "news_chunks")


def main():
    if not os.path.exists(NEWS_PARQUET):
        print(f"Missing {NEWS_PARQUET}")
        return
    df = pd.read_parquet(NEWS_PARQUET)
    # Index metadata to Meili
    meili = meilisearch.Client(MEILI_URL)
    try:
        meili.create_index(NEWS_INDEX, {"primaryKey": "url"})
    except Exception:
        pass
    docs = df[["url", "title", "published_at"]].to_dict(orient="records")
    # Ensure Mapping[str, Any] for type checkers with str keys
    docs_for_meili: Sequence[Mapping[str, Any]] = [
        {str(k): v for k, v in cast(dict[Any, Any], d).items()}
        for d in docs
    ]
    meili.index(NEWS_INDEX).add_documents(docs_for_meili)
    # Vectorize text and push to Qdrant
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = (df["clean_text"].fillna("").astype(str)).tolist()
    vecs = model.encode(texts, normalize_embeddings=True)
    client = QdrantClient(url=QDRANT_URL)
    try:
        client.get_collection(VEC_COLLECTION)
    except Exception:
        client.recreate_collection(VEC_COLLECTION, vectors_config=VectorParams(size=len(vecs[0]), distance=Distance.COSINE))
    ids: list[ExtendedPointId] = [int(i) for i in range(len(df))]
    vectors: list[list[float]] = [list(map(float, vecs[i].tolist())) for i in range(len(df))]
    payloads: list[Payload] = [
        {
            "url": str(df.iloc[i]["url"]),
            "title": str(df.iloc[i]["title"]),
        }
        for i in range(len(df))
    ]
    batch = Batch(ids=ids, vectors=vectors, payloads=payloads)
    client.upsert(VEC_COLLECTION, points=batch)
    print("Indexed", len(ids))


if __name__ == "__main__":
    main()
