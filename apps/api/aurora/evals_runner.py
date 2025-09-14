from __future__ import annotations

from typing import List, Dict, Any


def run_ragas_eval(questions: List[str]) -> Dict[str, Any]:
    """Run a RAG faithfulness evaluation over the given questions.

    Behavior:
    - If `ragas` and `datasets` are installed, compute faithfulness, answer relevancy, and context recall.
    - Otherwise, fall back to a lightweight heuristic using available endpoints (/copilot/ask and /tools/retrieve_docs).

    Returns a dict with keys: { ok, summary: {faithfulness, relevancy, recall}, details: [ ... ] }.
    """
    try:
        # Use in-process TestClient to avoid external HTTP dependency
        from fastapi.testclient import TestClient  # type: ignore
        from .main import app  # type: ignore
    except Exception as e:  # pragma: no cover
        return {"ok": False, "error": f"app unavailable: {e}"}

    client = TestClient(app)
    qs = [q for q in (questions or []) if isinstance(q, str) and q.strip()]
    if not qs:
        qs = ["Pinecone traction"]

    # Gather answers and contexts
    records: List[Dict[str, Any]] = []
    for q in qs[:50]:
        try:
            a = client.post("/copilot/ask", json={"question": q})
            ans = a.json() if a.status_code == 200 else {"answer": "", "sources": []}
        except Exception:
            ans = {"answer": "", "sources": []}
        try:
            r = client.get("/tools/retrieve_docs", params={"query": q, "limit": 6})
            docs = r.json().get("docs", []) if r.status_code == 200 else []
        except Exception:
            docs = []
        # contexts: best-effort text; fallback to URL strings
        ctx_texts: List[str] = []
        for d in docs:
            txt = (d.get("text") or d.get("title") or d.get("url") or "").strip()
            if txt:
                ctx_texts.append(txt)
        records.append({
            "question": q,
            "answer": ans.get("answer") or "",
            "contexts": ctx_texts or [u for u in ans.get("sources", []) if isinstance(u, str)],
            "sources": ans.get("sources", []) or [],
        })

    # Try real ragas path
    try:
        from ragas import evaluate  # type: ignore
        from ragas.metrics import faithfulness, answer_relevancy, context_recall  # type: ignore
        from datasets import Dataset  # type: ignore

        ds = Dataset.from_dict({
            "question": [r["question"] for r in records],
            "answer": [r["answer"] for r in records],
            "contexts": [r["contexts"] for r in records],
        })
        result = evaluate(
            ds,
            metrics=[faithfulness, answer_relevancy, context_recall],
        )
        # result is an EvaluationResult with scores and details
        scores = result.scores  # type: ignore[attr-defined]
        summary = {
            "faithfulness": float(scores.get("faithfulness", 0.0)),
            "relevancy": float(scores.get("answer_relevancy", 0.0)),
            "recall": float(scores.get("context_recall", 0.0)),
        }
        return {"ok": True, "summary": summary, "details": getattr(result, "items", [])}
    except Exception:
        # Heuristic fallback: approximate metrics using sources vs retrieved
        details = []
        f_vals: List[float] = []
        r_vals: List[float] = []
        c_vals: List[float] = []
        for rec in records:
            ctx = set([c for c in rec.get("contexts", []) if isinstance(c, str)])
            srcs = set([s for s in rec.get("sources", []) if isinstance(s, str)])
            # Faithfulness ~ 1 if at least one citation exists; 0 otherwise
            f = 1.0 if srcs else 0.0
            # Relevancy ~ Jaccard over token sets of answer and concatenated contexts (very rough)
            try:
                ans_tokens = set((rec.get("answer") or "").lower().split())
                ctx_tokens = set(" ".join(list(ctx)).lower().split())
                inter = len(ans_tokens & ctx_tokens)
                union = len(ans_tokens | ctx_tokens) or 1
                r = inter / union
            except Exception:
                r = 0.0
            # Context recall ~ fraction of citations present in retrieved pool (proxy)
            try:
                pool = set(ctx)
                c = (len(srcs & pool) / (len(srcs) or 1)) if srcs else 0.0
            except Exception:
                c = 0.0
            f_vals.append(f)
            r_vals.append(r)
            c_vals.append(c)
            details.append({
                "question": rec.get("question"),
                "faithfulness": round(f, 3),
                "relevancy": round(r, 3),
                "recall": round(c, 3),
            })
        def avg(xs: List[float]) -> float:
            return round(sum(xs) / max(1, len(xs)), 3)
        summary = {"faithfulness": avg(f_vals), "relevancy": avg(r_vals), "recall": avg(c_vals)}
        return {"ok": True, "summary": summary, "details": details, "note": "heuristic fallback; install 'ragas' for true metrics"}
