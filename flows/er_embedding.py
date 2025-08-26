import os
import ast
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer


COMPANIES_CSV = os.getenv("COMPANIES_CSV", "scripts/companies.csv")
NEWS_PARQUET = os.getenv("NEWS_PARQUET", "data/raw/news_items.parquet")
CURATED_COMPANIES = os.getenv("CURATED_COMPANIES", "data/curated/companies.parquet")
MODEL_NAME = os.getenv("ER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
THRESHOLD = float(os.getenv("ER_COSINE_THRESHOLD", "0.60"))


def load_companies():
    if os.path.exists(COMPANIES_CSV):
        return pd.read_csv(COMPANIES_CSV)
    # If no csv, synthesize a single ExampleAI company for the demo
    return pd.DataFrame([
        {"id": 1, "name": "ExampleAI", "website": "https://example.ai", "aliases": "[]", "segment": "vector_db", "country": "US"}
    ])


def normalize_aliases(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str) and x.strip():
        try:
            v = ast.literal_eval(x)
            if isinstance(v, list):
                return v
        except Exception:
            pass
        return [x]
    return []


def text_embed(model, texts):
    return model.encode(list(texts), normalize_embeddings=True)


def cosine(a: np.ndarray, b: np.ndarray):
    return float(np.dot(a, b))


def main():
    # Load companies and titles from news for candidate mentions
    companies = load_companies().copy()
    companies["aliases"] = companies["aliases"].apply(normalize_aliases)
    companies["candidate_names"] = companies.apply(lambda r: [r.get("name", "")] + list(r.get("aliases", [])), axis=1)

    if not os.path.exists(NEWS_PARQUET):
        print("Missing news parquet; writing curated companies from CSV only.")
        curated = companies[["id", "name", "website", "segment", "country", "aliases"]].rename(columns={"id": "canonical_id"})
        os.makedirs(os.path.dirname(CURATED_COMPANIES), exist_ok=True)
        curated.to_parquet(CURATED_COMPANIES, index=False)
        return

    news = pd.read_parquet(NEWS_PARQUET)
    titles = news["title"].fillna("").astype(str).tolist()

    model = SentenceTransformer(MODEL_NAME)
    title_vecs = text_embed(model, titles)

    rows = []
    for _, c in companies.iterrows():
        cand = [t for t in c["candidate_names"] if t]
        if not cand:
            continue
        cand_vecs = text_embed(model, cand)
        # Compute max cosine against all titles for each candidate alias/name
        best = 0.0
        for v in cand_vecs:
            sims = np.dot(title_vecs, v)
            score = float(np.max(sims)) if len(sims) else 0.0
            if score > best:
                best = score
        rows.append({
            "canonical_id": c.get("id", None) or 0,
            "name": c.get("name"),
            "website": c.get("website"),
            "segment": c.get("segment"),
            "country": c.get("country"),
            "aliases": c.get("aliases", []),
            "er_score": best,
            "provenance": "embedding_cosine",
        })

    curated = pd.DataFrame(rows)
    curated = curated[curated["er_score"] >= THRESHOLD]
    os.makedirs(os.path.dirname(CURATED_COMPANIES), exist_ok=True)
    curated.to_parquet(CURATED_COMPANIES, index=False)
    print("Wrote", CURATED_COMPANIES, len(curated))


if __name__ == "__main__":
    main()
