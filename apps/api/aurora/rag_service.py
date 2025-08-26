from qdrant_client import QdrantClient
from .config import settings
import importlib
from typing import Any, List, Dict, Optional, Tuple
from pathlib import Path
import json
from .clients import meili
from rapidfuzz import fuzz


def get_rag_index(collection: str = "docs"):
    try:
        li = importlib.import_module("llama_index")
        li_qdrant = importlib.import_module("llama_index.vector_stores.qdrant")
    except Exception as e:
        raise RuntimeError("LlamaIndex not installed or incompatible. Install dependencies to enable RAG.") from e

    client = QdrantClient(url=settings.qdrant_url) if settings.qdrant_url else None
    QdrantVectorStore: Any = getattr(li_qdrant, "QdrantVectorStore")
    StorageContext: Any = getattr(li, "StorageContext")
    VectorStoreIndex: Any = getattr(li, "VectorStoreIndex")
    if client is None:
        raise RuntimeError("Qdrant URL not configured")
    vs = QdrantVectorStore(client=client, collection_name=collection)
    storage = StorageContext.from_defaults(vector_store=vs)
    return VectorStoreIndex.from_vector_store(vs, storage_context=storage)


def get_llm(model: str = "llama3.1:8b"):
    try:
        li_ollama = importlib.import_module("llama_index.llms.ollama")
    except Exception as e:
        raise RuntimeError("Ollama LLM wrapper missing. Install llama-index and restart.") from e
    Ollama: Any = getattr(li_ollama, "Ollama")
    return Ollama(model=model, base_url=settings.ollama_base_url)


def _load_prompt() -> str:
    p = Path(__file__).resolve().parents[3] / "models" / "prompts" / "company_brief_prompt.txt"
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are an investment analyst. Synthesize insights ONLY from the provided context. "
            "Every claim must include a citation. Output valid JSON strictly."
        )


def _try_parse_json(text: str) -> Optional[dict]:
    if not isinstance(text, str):
        return None
    t = text.strip()
    # Strip code fences if present
    if t.startswith("```"):
        t = t.strip("`\n ")
        if t.lower().startswith("json"):
            t = t[4:].lstrip()
    try:
        return json.loads(t)
    except Exception:
        return None


def answer_with_citations(question: str) -> dict:
    # Hybrid: keyword search via Meilisearch
    hits: List[Dict] = []
    if meili:
        try:
            res = meili.index("companies").search(question, {"limit": 5})
            for h in res.get("hits", []):
                hits.append({"source": "meilisearch", **h})
        except Exception:
            pass

    # Vector search via LlamaIndex/Qdrant
    prompt = _load_prompt()
    try:
        index = get_rag_index()
        # Retrieve a bit more, we'll rerank down
        query_engine = index.as_query_engine(similarity_top_k=8)
        _ = get_llm()  # ensure LLM is available
        # Prepend system prompt guidance
        full_q = f"{prompt}\n\nQuestion: {question}\nReturn strict JSON only."
        resp = query_engine.query(full_q)
    except Exception:
        # If vector path fails, degrade gracefully
        resp = "Insufficient evidence"
    sources = []  # raw nodes capture
    for node in getattr(resp, "source_nodes", []) or []:
        meta = getattr(node.node, "metadata", {}) or {}
        text = getattr(node.node, "text", None)
        vscore = getattr(node, "score", None)
        sources.append({
            "source_id": getattr(node.node, "node_id", None),
            "text": text,
            "vector_score": vscore,
            **meta,
        })

    # Merge and dedupe sources
    merged_sources = []
    seen = set()
    for s in sources + hits:
        key = s.get("url") or s.get("source_id") or s.get("id")
        if key and key not in seen:
            merged_sources.append(s)
            seen.add(key)
    # Rerank sources by combined score: 0.6 * vector_sim + 0.4 * keyword_fuzz
    # vector_score is expected in [0,1]; keyword fuzz in [0,100]
    def _score_components(src: Dict) -> Tuple[float, float]:
        title = str(src.get("title") or "")
        url = str(src.get("url") or "")
        text = str(src.get("text") or "")
        # Keyword-based fuzzy score (0..100)
        fuzz_score = float(max(
            fuzz.token_set_ratio(question, title),
            fuzz.partial_ratio(question, url),
            fuzz.token_set_ratio(question, text[:256])
        ))
        # Vector similarity score (0..1)
        v = src.get("vector_score")
        try:
            v = float(v) if v is not None else 0.0
        except Exception:
            v = 0.0
        v = max(0.0, min(1.0, v))
        return v, fuzz_score

    def _hybrid_score(src: Dict) -> float:
        v, fz = _score_components(src)
        return 0.6 * v + 0.4 * (fz / 100.0)

    merged_sources.sort(key=_hybrid_score, reverse=True)
    # Compress sources into citations with short snippets
    citations: List[Dict] = []
    for s in merged_sources[:6]:
        snippet = (str(s.get("text") or "").strip().replace("\n", " ")[:200]) if s.get("text") else None
        entry = {k: v for k, v in s.items() if k != "text"}
        # include audit scores if available
        try:
            v, fz = _score_components(s)
            entry["vector_score"] = v
            entry["keyword_fuzz"] = fz
            entry["hybrid_score"] = _hybrid_score(s)
        except Exception:
            pass
        if snippet:
            entry["snippet"] = snippet
        citations.append(entry)

    # Attempt JSON parse for strict schema path
    maybe = _try_parse_json(str(resp)) if not isinstance(resp, dict) else resp
    answer_payload = maybe if maybe is not None else (resp if isinstance(resp, dict) else str(resp))
    if not citations:
        answer_payload = "Insufficient evidence"
    return {"answer": answer_payload, "sources": citations}


def seed_sample_docs():
    try:
        li = importlib.import_module("llama_index")
        li_hf = importlib.import_module("llama_index.embeddings.huggingface")
        li_qdrant = importlib.import_module("llama_index.vector_stores.qdrant")
    except Exception:
        return {"status": "skipped", "reason": "llama-index not installed"}

    VectorStoreIndex: Any = getattr(li, "VectorStoreIndex")
    StorageContext: Any = getattr(li, "StorageContext")
    Document: Any = getattr(li, "Document")
    HuggingFaceEmbedding: Any = getattr(li_hf, "HuggingFaceEmbedding")
    QdrantVectorStore: Any = getattr(li_qdrant, "QdrantVectorStore")

    if not settings.qdrant_url:
        return {"status": "skipped", "reason": "qdrant not configured"}
    client = QdrantClient(url=settings.qdrant_url)
    vs = QdrantVectorStore(client=client, collection_name="docs")
    storage = StorageContext.from_defaults(vector_store=vs)
    docs = [
        Document(
            text=(
                "ExampleAI is a startup building a vector database for LLM applications, "
                "operating in the Vector DB segment of GenAI infrastructure."
            ),
            metadata={"source": "seed", "url": "https://example.ai"},
        )
    ]
    embed = HuggingFaceEmbedding(model_name="BAAI/bge-small-en")
    VectorStoreIndex.from_documents(docs, storage_context=storage, embed_model=embed)
    return {"status": "seeded", "count": len(docs)}
