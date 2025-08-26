import os
import json
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
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
    meili.index(NEWS_INDEX).add_documents(docs)
    # Vectorize text and push to Qdrant
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = (df["clean_text"].fillna("").astype(str)).tolist()
    vecs = model.encode(texts, normalize_embeddings=True)
    client = QdrantClient(url=QDRANT_URL)
    try:
        client.get_collection(VEC_COLLECTION)
    except Exception:
        client.recreate_collection(VEC_COLLECTION, vectors_config=VectorParams(size=len(vecs[0]), distance=Distance.COSINE))
    points = [{"id": i, "vector": vecs[i].tolist(), "payload": {"url": df.iloc[i]["url"], "title": df.iloc[i]["title"]}} for i in range(len(df))]
    client.upsert(VEC_COLLECTION, points=points)
    print("Indexed", len(points))


if __name__ == "__main__":
    main()
