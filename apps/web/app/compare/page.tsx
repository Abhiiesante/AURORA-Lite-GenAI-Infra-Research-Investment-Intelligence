"use client";
export const dynamic = "force-dynamic";
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Compare() {
  const [a, setA] = useState("1");
  const [b, setB] = useState("2");
  const [result, setResult] = useState(null as any);
  const [snips, setSnips] = useState({} as any); // url -> title snippet
  // Initialize from URL params if present
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    const qa = url.searchParams.get("a");
    const qb = url.searchParams.get("b");
    if (qa) setA(qa);
    if (qb) setB(qb);
  }, []);
  const run = async () => {
    const { data } = await axios.post(`${api}/compare`, { companies: [a, b], metrics: ["signal_score","stars_30d","commits_30d","mentions_7d"] });
    setResult(data);
  };
  // Auto-run when params were provided
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (url.searchParams.get("a") || url.searchParams.get("b")) {
      run();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const shareUrl = useMemo(() => {
    if (typeof window === "undefined") return "";
    const url = new URL(window.location.href);
    url.searchParams.set("a", a || "");
    url.searchParams.set("b", b || "");
    return url.toString();
  }, [a, b]);
  const copyShare = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      alert("Link copied");
    } catch {
      // no-op
    }
  };
  const ensureSnippet = async (u: string) => {
    if (!u || snips[u]) return;
    try {
      const res = await fetch(`${api}/tools/snippet?url=${encodeURIComponent(u)}`);
      const j = await res.json();
      const title = j?.title || u;
      setSnips((prev:any)=> ({ ...prev, [u]: title }));
    } catch {
      setSnips((prev:any)=> ({ ...prev, [u]: u }));
    }
  };
  return (
    <main style={{ padding: 24 }}>
      <h1>Compare</h1>
      <div style={{ display: 'flex', gap: 8 }}>
  <input value={a} onChange={(e: any)=>setA(e.target.value)} placeholder="Company A id" />
  <input value={b} onChange={(e: any)=>setB(e.target.value)} placeholder="Company B id" />
        <button onClick={run}>Run</button>
        <button onClick={copyShare} title="Copy shareable link">Share</button>
      </div>
      {result && (
        <section style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <h3>Table</h3>
            <table style={{ borderCollapse: 'collapse' }}>
              <thead><tr><th>Metric</th><th>A</th><th>B</th><th>Δ</th></tr></thead>
              <tbody>
                {(result.comparisons||[]).map((r:any)=> (
                  <tr key={r.metric}><td>{r.metric}</td><td>{String(r.a)}</td><td>{String(r.b)}</td><td>{r.delta}</td></tr>
                ))}
              </tbody>
            </table>
            <p style={{ marginTop: 8 }}>Narrative: {result.answer}</p>
          </div>
          <div>
            <h3>Sources</h3>
            <ul>
              {(result.sources||[]).map((u:string)=> (
                <li key={u}>
                  <a href={u} target="_blank" rel="noreferrer" title={snips[u] || u} onMouseEnter={()=>ensureSnippet(u)}>{u}</a>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </main>
  );
}
