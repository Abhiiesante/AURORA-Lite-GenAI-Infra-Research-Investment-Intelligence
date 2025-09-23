"use client";
import ClusterExplorer from "./ClusterExplorer";
import { useExplorerData } from "./hooks";
import { useReducedMotion } from "../bridge/useReducedMotion";
import { useMemo, useRef, useState } from "react";

export default function ExplorerPage(){
  const reduced = useReducedMotion();
  const [sectorFilter, setSectorFilter] = useState([] as string[]);
  const { data, isLoading, error } = useExplorerData({ sector: sectorFilter });
  const [selected, setSelected] = useState(null as string | null);
  const explorerApi = useRef(null as unknown as { snapshot: () => string; resetCamera: () => void } | null);
  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];
  const sectors = useMemo(() => ["tech","healthcare","finance","energy","consumer"], []);
  return (
    <main style={{ background: "var(--bg-01)", minHeight: "100vh" }}>
      <header style={{ display: "flex", alignItems: "center", gap: 12, padding: 16 }}>
        <h1 style={{ fontFamily: "Orbitron, sans-serif", color: "var(--aurora-cyan)", textShadow: "0 0 8px rgba(0,240,255,0.3)", fontSize: 28 }}>Company Cluster Explorer</h1>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
           {sectors.map((s: string) => (
             <button key={s} onClick={()=> setSectorFilter((prev: string[])=> prev.includes(s) ? prev.filter((x: string)=>x!==s) : [...prev, s])}
              aria-pressed={sectorFilter.includes(s)}
              style={{ padding: "6px 10px", borderRadius: 999, border: "1px solid rgba(255,255,255,0.2)", color: "var(--starlight)", background: sectorFilter.includes(s) ? "rgba(0,240,255,0.15)" : "transparent" }}>{s}</button>
          ))}
        </div>
      </header>
      <section style={{ display: "grid", gridTemplateColumns: "320px 1fr 360px", gap: 16, alignItems: "start", maxWidth: 1680, margin: "0 auto", padding: 16 }}>
        <aside aria-label="Cluster KPIs" style={{ position: "sticky", top: 16, height: "calc(70vh + 160px)", padding: 12,
          backdropFilter: "blur(var(--glass-blur))", WebkitBackdropFilter: "blur(var(--glass-blur))",
          background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 16, color: "var(--starlight)" }}>
          <h2 style={{ fontSize: 14, opacity: 0.9 }}>Cluster</h2>
          <ul style={{ fontSize: 12, lineHeight: 1.8 }}>
            <li>Companies: {nodes.length}</li>
            <li>Edges: {edges.length}</li>
            <li>Avg Signal: {nodes.length ? Math.round(nodes.reduce((a:any,n:any)=>a+n.signal,0)/nodes.length) : 0}</li>
          </ul>
          <div style={{ marginTop: 12 }}>Filters</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
             {sectors.map((s: string) => (
               <button key={s} onClick={()=> setSectorFilter((prev: string[])=> prev.includes(s) ? prev.filter((x: string)=>x!==s) : [...prev, s])}
                aria-pressed={sectorFilter.includes(s)}
                style={{ padding: "6px 10px", borderRadius: 999, border: "1px solid rgba(255,255,255,0.2)", color: "var(--starlight)", background: sectorFilter.includes(s) ? "rgba(0,240,255,0.15)" : "transparent" }}>{s}</button>
            ))}
          </div>
        </aside>
        <div>
          <ClusterExplorer
            nodes={nodes}
            edges={edges}
            reducedMotion={reduced}
            onNodeClick={(id)=> setSelected(id)}
            onReady={(api)=> { explorerApi.current = api; }}
          />
          {(isLoading || error) && (
            <div role="status" aria-live="polite" style={{position:"absolute", top:16, right:16, padding:"6px 10px", background:"rgba(0,0,0,0.5)", border:"1px solid rgba(255,255,255,0.15)", borderRadius:8, color:"var(--starlight)", fontSize:12}}>
              {isLoading ? "Loading graph…" : "Graph data unavailable"}
            </div>
          )}
          {/* Floating overlay controls */}
          <div aria-label="View controls" style={{ position:"absolute", top:16, left:16, display:"flex", gap:8 }}>
            <input type="search" placeholder="Search companies" aria-label="Search" style={{ padding:"6px 10px", borderRadius:8, border:"1px solid rgba(255,255,255,0.2)", background:"rgba(0,0,0,0.4)", color:"var(--starlight)" }} />
          </div>
          <div aria-label="Camera controls" style={{ position:"absolute", top:16, right:16, display:"flex", gap:8 }}>
            <button onClick={()=> explorerApi.current?.resetCamera()} style={{ padding:"6px 10px", borderRadius:8, border:"1px solid rgba(255,255,255,0.2)", background:"rgba(0,0,0,0.4)", color:"var(--starlight)" }}>Reset</button>
            <button onClick={()=> { const dataUrl = explorerApi.current?.snapshot(); if (dataUrl) downloadDataUrl(dataUrl, "cluster.png"); }} style={{ padding:"6px 10px", borderRadius:8, border:"1px solid rgba(255,255,255,0.2)", background:"rgba(0,0,0,0.4)", color:"var(--starlight)" }}>Snapshot</button>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button onClick={()=> { const dataUrl = explorerApi.current?.snapshot(); if (dataUrl) downloadDataUrl(dataUrl, "cluster.png"); }} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.2)", background: "transparent", color: "var(--starlight)" }}>Snapshot</button>
            <button onClick={()=> exportJSON({ nodes, edges })} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.2)", background: "transparent", color: "var(--starlight)" }}>Export</button>
            <button style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.2)", background: "transparent", color: "var(--starlight)" }}>Compare</button>
            <div style={{ marginLeft: "auto", color: "var(--starlight)", fontSize: 12, opacity: 0.85 }}>Time: realtime</div>
          </div>
        </div>
        <aside aria-label="Company detail" style={{ position: "sticky", top: 16, height: "calc(70vh + 160px)", padding: 12,
          backdropFilter: "blur(var(--glass-blur))", WebkitBackdropFilter: "blur(var(--glass-blur))",
          background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 16, color: "var(--starlight)" }}>
          <h2 style={{ fontSize: 14, opacity: 0.9 }}>Company</h2>
          <div style={{ fontSize: 12, opacity: 0.8 }}>{selected ? `Selected: ${selected}` : "Select a node to see details"}</div>
        </aside>
      </section>
    </main>
  );
}

function downloadDataUrl(dataUrl: string, filename: string){
  const a = document.createElement('a');
  a.href = dataUrl; a.download = filename; a.click();
}
function exportJSON(obj: any){
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  downloadDataUrl(url, 'cluster.json');
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}
