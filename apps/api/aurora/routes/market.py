from fastapi import APIRouter
from ..clients import neo4j

router = APIRouter()


@router.get("/graph")
def graph():
    try:
        nodes = []
        edges = []
        if neo4j is None:
            raise RuntimeError("neo4j client not configured")
        with neo4j.session() as s:
            res = s.run(
                """
                MATCH (a)-[r]->(b)
                RETURN labels(a) as a_labels, a.id as a_id, a.label as a_label,
                       a.segment as a_segment, a.signal_score as a_signal,
                       type(r) as rel,
                       labels(b) as b_labels, b.id as b_id, b.label as b_label,
                       b.segment as b_segment, b.signal_score as b_signal
                LIMIT 500
                """
            )
            seen = set()
            for rec in res:
                a_id = rec["a_id"]; b_id = rec["b_id"]
                if a_id and a_id not in seen:
                    nodes.append({
                        "id": a_id, "label": rec["a_label"],
                        "type": (rec["a_labels"][0] if rec["a_labels"] else "node"),
                        "segment": rec.get("a_segment"), "signal_score": rec.get("a_signal")
                    })
                    seen.add(a_id)
                if b_id and b_id not in seen:
                    nodes.append({
                        "id": b_id, "label": rec["b_label"],
                        "type": (rec["b_labels"][0] if rec["b_labels"] else "node"),
                        "segment": rec.get("b_segment"), "signal_score": rec.get("b_signal")
                    })
                    seen.add(b_id)
                edges.append({"source": a_id, "target": b_id, "type": rec["rel"]})
        if nodes:
            return {"nodes": nodes, "edges": edges}
    except Exception:
        pass
    # Fallback static graph
    return {
        "nodes": [
            {"id": "segment:vector_db", "label": "Vector DB", "type": "Segment"},
            {"id": "company:ExampleAI", "label": "ExampleAI", "type": "Company"},
        ],
        "edges": [
            {"source": "segment:vector_db", "target": "company:ExampleAI", "type": "OPERATES_IN"}
        ],
    }
