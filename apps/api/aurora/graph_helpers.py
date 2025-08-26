from __future__ import annotations

from typing import Dict, List, Optional


def rebuild_comention_edges() -> Dict[str, int | bool]:
    """Attempt to rebuild co-mention edges in Neo4j if configured.
    Safe no-op when driver isn't available or settings are missing.
    """
    try:
        from .config import settings  # type: ignore
        if not getattr(settings, "neo4j_url", None):  # type: ignore[attr-defined]
            return {"ok": False, "edges": 0}
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception:
            return {"ok": False, "edges": 0}
        auth = None
        if getattr(settings, "neo4j_user", None) and getattr(settings, "neo4j_password", None):  # type: ignore[attr-defined]
            auth = (settings.neo4j_user, settings.neo4j_password)
        driver = GraphDatabase.driver(settings.neo4j_url, auth=auth)
        cypher = (
            "MATCH (n:NewsItem)<-[:MENTIONED_IN]-(c1:Company),"
            "      (n)<-[:MENTIONED_IN]-(c2:Company) "
            "WHERE id(c1) < id(c2) "
            "WITH c1, c2, count(n) as cnt "
            "MERGE (c1)-[r:CO_MENTIONED]->(c2) "
            "SET r.count = cnt, r.updated_at = timestamp()"
        )
        with driver.session() as session:  # type: ignore
            res = session.run(cypher)
        try:
            driver.close()
        except Exception:
            pass
        return {"ok": True, "edges": 0}
    except Exception:
        return {"ok": False, "edges": 0}


def query_ego(company_id: str) -> Dict[str, object]:
    """Return a tiny ego graph: node plus optionally its immediate neighbors if Neo4j is configured.
    Safe no-op returning only the node when unavailable.
    """
    try:
        from .config import settings  # type: ignore
        if not getattr(settings, "neo4j_url", None):  # type: ignore[attr-defined]
            return {"nodes": [{"id": str(company_id)}], "edges": []}
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception:
            return {"nodes": [{"id": str(company_id)}], "edges": []}
        auth = None
        if getattr(settings, "neo4j_user", None) and getattr(settings, "neo4j_password", None):  # type: ignore[attr-defined]
            auth = (settings.neo4j_user, settings.neo4j_password)
        driver = GraphDatabase.driver(settings.neo4j_url, auth=auth)
        cypher = (
            "MATCH (c:Company {id: $cid})- [r:CO_MENTIONED] - (n:Company) "
            "RETURN c.id as src, n.id as dst, r.count as w LIMIT 50"
        )
        nodes = [{"id": str(company_id)}]
        edges: List[Dict[str, object]] = []
        try:
            with driver.session() as session:  # type: ignore
                res = session.run(cypher, cid=str(company_id))
                for rec in res:
                    dst = rec["dst"]
                    if not any(n.get("id") == dst for n in nodes):
                        nodes.append({"id": dst})
                    edges.append({"source": str(company_id), "target": dst, "weight": rec.get("w", 0)})
        finally:
            try:
                driver.close()
            except Exception:
                pass
        return {"nodes": nodes, "edges": edges}
    except Exception:
        return {"nodes": [{"id": str(company_id)}], "edges": []}


def query_derived(company_id: str, window: str = "90d") -> Dict[str, object]:
    """Return derived edges for a company in a time window if available.
    Safe no-op returning empty edges otherwise.
    """
    try:
        from .config import settings  # type: ignore
        if not getattr(settings, "neo4j_url", None):  # type: ignore[attr-defined]
            return {"company": str(company_id), "edges": [], "window": window}
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception:
            return {"company": str(company_id), "edges": [], "window": window}
        auth = None
        if getattr(settings, "neo4j_user", None) and getattr(settings, "neo4j_password", None):  # type: ignore[attr-defined]
            auth = (settings.neo4j_user, settings.neo4j_password)
        driver = GraphDatabase.driver(settings.neo4j_url, auth=auth)
        cypher = (
            "MATCH (c:Company {id: $cid})- [r:CO_MENTIONED] - (n:Company) "
            "WHERE r.updated_at >= timestamp() - 90*24*3600*1000 "
            "RETURN c.id as src, n.id as dst, r.count as w LIMIT 100"
        )
        edges: List[Dict[str, object]] = []
        try:
            with driver.session() as session:  # type: ignore
                res = session.run(cypher, cid=str(company_id))
                for rec in res:
                    edges.append({"source": rec["src"], "target": rec["dst"], "weight": rec.get("w", 0)})
        finally:
            try:
                driver.close()
            except Exception:
                pass
        return {"company": str(company_id), "edges": edges, "window": window}
    except Exception:
        return {"company": str(company_id), "edges": [], "window": window}


def query_similar(company_id: str, limit: int = 5) -> Dict[str, object]:
    """Return a list of similar companies, best-effort.
    Without Neo4j, return a stub empty list.
    """
    try:
        from .config import settings  # type: ignore
        if not getattr(settings, "neo4j_url", None):  # type: ignore[attr-defined]
            return {"company": str(company_id), "similar": [], "limit": int(limit)}
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception:
            return {"company": str(company_id), "similar": [], "limit": int(limit)}
        auth = None
        if getattr(settings, "neo4j_user", None) and getattr(settings, "neo4j_password", None):  # type: ignore[attr-defined]
            auth = (settings.neo4j_user, settings.neo4j_password)
        driver = GraphDatabase.driver(settings.neo4j_url, auth=auth)
        # Use co-mention weight as a proxy for similarity
        cypher = (
            "MATCH (c:Company {id: $cid})- [r:CO_MENTIONED] - (n:Company) "
            "RETURN n.id as id, r.count as w ORDER BY w DESC LIMIT $lim"
        )
        sims: List[Dict[str, object]] = []
        try:
            with driver.session() as session:  # type: ignore
                res = session.run(cypher, cid=str(company_id), lim=int(limit))
                for rec in res:
                    sims.append({"id": rec["id"], "score": rec.get("w", 0)})
        finally:
            try:
                driver.close()
            except Exception:
                pass
        return {"company": str(company_id), "similar": sims, "limit": int(limit)}
    except Exception:
        return {"company": str(company_id), "similar": [], "limit": int(limit)}


def query_investors(company_id: str) -> Dict[str, object]:
    """Return investors for a company if available; safe no-op otherwise."""
    try:
        from .config import settings  # type: ignore
        if not getattr(settings, "neo4j_url", None):  # type: ignore[attr-defined]
            return {"company": str(company_id), "investors": []}
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception:
            return {"company": str(company_id), "investors": []}
        auth = None
        if getattr(settings, "neo4j_user", None) and getattr(settings, "neo4j_password", None):  # type: ignore[attr-defined]
            auth = (settings.neo4j_user, settings.neo4j_password)
        driver = GraphDatabase.driver(settings.neo4j_url, auth=auth)
        cypher = (
            "MATCH (i:Investor)-[:INVESTED_IN]->(c:Company {id: $cid}) "
            "RETURN i.name as name LIMIT 50"
        )
        names: List[str] = []
        try:
            with driver.session() as session:  # type: ignore
                res = session.run(cypher, cid=str(company_id))
                for rec in res:
                    names.append(str(rec["name"]))
        finally:
            try:
                driver.close()
            except Exception:
                pass
        return {"company": str(company_id), "investors": names}
    except Exception:
        return {"company": str(company_id), "investors": []}


def query_talent(company_id: str) -> Dict[str, object]:
    """Return shared-talent edges if available; safe no-op otherwise."""
    try:
        from .config import settings  # type: ignore
        if not getattr(settings, "neo4j_url", None):  # type: ignore[attr-defined]
            return {"company": str(company_id), "talent_links": []}
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception:
            return {"company": str(company_id), "talent_links": []}
        auth = None
        if getattr(settings, "neo4j_user", None) and getattr(settings, "neo4j_password", None):  # type: ignore[attr-defined]
            auth = (settings.neo4j_user, settings.neo4j_password)
        driver = GraphDatabase.driver(settings.neo4j_url, auth=auth)
        cypher = (
            "MATCH (p:Person)-[:WORKED_AT]->(c1:Company {id: $cid}),"
            "      (p)-[:WORKED_AT]->(c2:Company) "
            "WHERE c1 <> c2 RETURN c2.id as other, count(p) as cnt ORDER BY cnt DESC LIMIT 50"
        )
        links: List[Dict[str, object]] = []
        try:
            with driver.session() as session:  # type: ignore
                res = session.run(cypher, cid=str(company_id))
                for rec in res:
                    links.append({"company": rec["other"], "count": rec.get("cnt", 0)})
        finally:
            try:
                driver.close()
            except Exception:
                pass
        return {"company": str(company_id), "talent_links": links}
    except Exception:
        return {"company": str(company_id), "talent_links": []}
