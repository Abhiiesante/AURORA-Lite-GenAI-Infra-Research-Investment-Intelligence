from __future__ import annotations

import asyncio
import time
import uuid
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ..clients import meili

router = APIRouter()

# Very small in-memory job registry for demo/prototype
_JOBS: Dict[str, Dict[str, object]] = {}


@router.get("/search")
def cmdk_search(q: str = Query("", description="Query string"), limit: int = 12):
    started = time.time()
    results: List[dict] = []
    try:
        if meili:
            idx = meili.index("companies")
            res = idx.search(q, {"limit": limit})
            for h in (res.get("hits") or [])[:limit]:
                results.append(
                    {
                        "id": str(h.get("id") or h.get("url") or uuid.uuid4().hex),
                        "type": h.get("type") or "company",
                        "title": h.get("canonical_name") or h.get("title") or h.get("url") or "Untitled",
                        "subtitle": h.get("description") or None,
                        "score": h.get("_score") or h.get("score"),
                        "actions": [{"id": "open", "label": "Open"}, {"id": "memo", "label": "Generate Memo"}],
                        "thumbnail_url": h.get("thumbnail_url") or None,
                    }
                )
    except Exception:
        # Meili not configured or failed; fall back to minimal mock list
        base = [
            {"id": "company:pinecone", "type": "company", "title": "Pinecone", "subtitle": "Vector DB — Managed service"},
            {"id": "topic:vector-db", "type": "topic", "title": "Vector Databases"},
            {"id": "company:qdrant", "type": "company", "title": "Qdrant", "subtitle": "Open-source vector search"},
            {"id": "company:meilisearch", "type": "company", "title": "Meilisearch", "subtitle": "Blazing-fast search"},
            {"id": "action:compare", "type": "command", "title": ">compare", "subtitle": "Compare companies"},
        ]
        results = [
            {**r, "actions": [{"id": "open", "label": "Open"}, {"id": "memo", "label": "Generate Memo"}]}
            for r in base
            if (not q) or (str(r.get("title", "")).lower().find(q.lower()) >= 0)
        ][:limit]

    took_ms = int((time.time() - started) * 1000)
    suggestions = ([f"{q} funding", f"{q} memo"] if q else ["pinecone.io", "pinecone funding"])  # minimal suggestions
    return {"query": q, "results": results, "suggestions": suggestions, "took_ms": took_ms}


@router.get("/thumbnail")
def cmdk_thumbnail(entity: str = Query("entity"), size: str = Query("160x96")):
    try:
        w_s, h_s = size.split("x")
        w, h = int(w_s), int(h_s)
    except Exception:
        w, h = 160, 96
    # Simple SVG data URL; frontend treats as PNG URL for convenience
    label = entity
    font = max(10, int(h * 0.22))
    svg = (
        f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{w}\" height=\"{h}\" viewBox=\"0 0 {w} {h}\">"
        f"<defs><linearGradient id=\"g\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop offset=\"0%\" stop-color=\"#0b1220\"/><stop offset=\"100%\" stop-color=\"#071017\"/></linearGradient></defs>"
        f"<rect width=\"100%\" height=\"100%\" fill=\"url(#g)\"/>"
        f"<text x=\"50%\" y=\"50%\" dominant-baseline=\"middle\" text-anchor=\"middle\" fill=\"rgba(0,240,255,0.85)\" font-family=\"Roboto Mono, monospace\" font-size=\"{font}\">{label}</text>"
        f"</svg>"
    )
    from urllib.parse import quote

    data_url = f"data:image/svg+xml;charset=utf-8,{quote(svg)}"
    return {"pngUrl": data_url, "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cacheHit": False}


@router.post("/command")
def cmdk_command(payload: dict):  # expects { cmd: str, payload: any }
    cmd = str(payload.get("cmd") or "").strip()
    job_id = uuid.uuid4().hex
    # Seed a fake job that completes shortly; status polled/streamed by /stream
    _JOBS[job_id] = {"cmd": cmd, "state": "queued", "progress": 0, "created_at": time.time()}

    async def _advance():
        # Simulate small progress then done
        try:
            _JOBS[job_id]["state"] = "running"
            for p in (15, 35, 65, 85):
                _JOBS[job_id]["progress"] = p
                await asyncio.sleep(0.4)
            _JOBS[job_id]["progress"] = 100
            _JOBS[job_id]["state"] = "done"
            _JOBS[job_id]["result"] = {"ok": True}
        except Exception:
            _JOBS[job_id]["state"] = "error"

    try:
        # Fire-and-forget background task (only works under async server)
        loop = asyncio.get_event_loop()
        loop.create_task(_advance())
    except RuntimeError:
        # If no loop, complete immediately
        _JOBS[job_id]["state"] = "done"
        _JOBS[job_id]["progress"] = 100

    return {"jobId": job_id, "statusUrl": f"/cmdk/stream?job_id={job_id}", "estimatedSeconds": 2}


@router.get("/stream")
async def cmdk_stream(job_id: Optional[str] = None):
    async def gen() -> AsyncGenerator[bytes, None]:
        # Minimal SSE stream; if job_id provided, emit its progress and completion
        headers = b"event: ping\n\n"
        yield headers
        last_state = None
        started = time.time()
        while True:
            if job_id:
                st = _JOBS.get(job_id)
                if not st:
                    # Briefly wait for job to be inserted
                    await asyncio.sleep(0.1)
                    st = _JOBS.get(job_id)
                if st:
                    state = st.get("state")
                    prog = st.get("progress", 0)
                    if state != last_state:
                        yield f"event: state\ndata: {{\"jobId\":\"{job_id}\",\"state\":\"{state}\"}}\n\n".encode()
                        last_state = state
                    # Throttle progress events
                    yield f"event: progress\ndata: {{\"jobId\":\"{job_id}\",\"progress\":{int(prog)} }}\n\n".encode()
                    if state in ("done", "error"):
                        yield f"event: done\ndata: {{\"jobId\":\"{job_id}\",\"ok\":{str(state== 'done').lower()} }}\n\n".encode()
                        break
            # Keep-alive and timeout after 30s
            yield b"event: keepalive\ndata: {}\n\n"
            if (time.time() - started) > 30:
                break
            await asyncio.sleep(0.6)

    return StreamingResponse(gen(), media_type="text/event-stream")
