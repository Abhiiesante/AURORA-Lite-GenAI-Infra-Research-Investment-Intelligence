import { NextRequest, NextResponse } from "next/server";

const upstream = process.env.NEXT_PUBLIC_API_URL;

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const q = searchParams.get("q") || "";
  const limit = Number(searchParams.get("limit") || 12);
  const scope = searchParams.get("scope") || "global";
  const started = Date.now();

  // If upstream is available and has /search, try proxy
  if (upstream) {
    try {
      const u = new URL("/search", upstream);
      u.searchParams.set("q", q);
      u.searchParams.set("limit", String(limit));
  // Disable caching for dev proxy; use standard RequestInit to satisfy TS
  const r = await fetch(u, { cache: "no-store" });
      if (r.ok) {
        const data = await r.json();
        const mapped = {
          query: q,
          results: (data.hits || []).slice(0, limit).map((h: any) => ({
            id: h.id || h.url || String(Math.random()),
            type: h.type || "company",
            title: h.canonical_name || h.title || h.url,
            subtitle: h.subtitle || h.description || undefined,
            score: h._score || h.score || undefined,
            actions: [{ id: "open", label: "Open" }, { id: "memo", label: "Generate Memo" }],
            thumbnail_url: h.thumbnail_url || undefined,
          })),
          suggestions: data.suggestions || [],
          took_ms: Date.now() - started,
        };
        return NextResponse.json(mapped);
      }
    } catch {}
  }

  // Fallback mock suggestions
  const base = [
    { id: "company:pinecone", type: "company", title: "Pinecone", subtitle: "Vector DB — Managed service" },
    { id: "topic:vector-db", type: "topic", title: "Vector Databases" },
    { id: "company:qdrant", type: "company", title: "Qdrant", subtitle: "Open-source vector search" },
    { id: "company:meilisearch", type: "company", title: "Meilisearch", subtitle: "Blazing-fast search" },
    { id: "action:compare", type: "command", title: ">compare", subtitle: "Compare companies" },
  ];
  const results = base
    .filter((r) => !q || r.title.toLowerCase().includes(q.toLowerCase()))
    .slice(0, limit)
    .map((r) => ({ ...r, actions: [{ id: "open", label: "Open" }, { id: "memo", label: "Generate Memo" }] }));
  const body = { query: q, results, suggestions: q ? [q + " funding", q + " memo"] : ["pinecone.io", "pinecone funding"], took_ms: Date.now() - started };
  return NextResponse.json(body);
}
