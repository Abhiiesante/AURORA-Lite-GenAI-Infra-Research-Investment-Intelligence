"use client";
/// <reference path="../../types/shims.d.ts" />
import dyn from "next/dynamic";
import React, { useEffect, useRef, useState } from "react";
import axios from "axios";

const CytoscapeComponent = dyn(() => import("react-cytoscapejs"), { ssr: false });
const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MarketMap() {
  type View = { name: string; segment: string; minSignal: number; elements: any[] };
  const [elements, setElements] = useState([] as any[]);
  const [segment, setSegment] = useState("");
  const [minSignal, setMinSignal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(200);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(null as number | null);
  const [views, setViews] = useState([] as View[]);
  const [selectedView, setSelectedView] = useState("");
  const cyRef = useRef(null as any);
  const sentinelRef = useRef(null as any);

  const toKey = (el: any) => {
    if (el?.data?.id) return `n:${el.data.id}`;
    if (el?.data?.source && el?.data?.target) return `e:${el.data.source}->${el.data.target}`;
    return Math.random().toString(36);
  };

  const load = (reset: boolean = false) => {
    const params = new URLSearchParams();
    if (segment) params.set("segment", segment);
    if (minSignal) params.set("min_signal", String(minSignal));
    params.set("page", String(reset ? 1 : page));
    params.set("size", String(size));
    axios.get(`${api}/market/realtime?${params.toString()}`)
      .then((res: any) => {
        const { nodes, edges, pagination } = res.data || {};
        const fresh = [
          ...nodes.map((n: any) => ({ data: { id: n.id, label: n.label, type: n.type, segment: n.segment, signal: n.signal_score || 0 } })),
          ...edges.map((e: any) => ({ data: { source: e.source, target: e.target } }))
        ];
        if (reset) {
          setElements(fresh);
        } else {
          setElements((prev: any[]) => {
            const map = new Map<string, any>();
            for (const el of prev) map.set(toKey(el), el);
            for (const el of fresh) map.set(toKey(el), el);
            return Array.from(map.values());
          });
        }
        if (pagination) {
          setHasMore(!!pagination.has_more);
          setTotal(typeof pagination.total === 'number' ? pagination.total : null);
          setPage((p: number) => (reset ? 2 : p + 1));
        }
      })
      .catch(() => {
        setElements([
          { data: { id: "segment:vector_db", label: "Vector DB" } },
          { data: { id: "company:ExampleAI", label: "ExampleAI" } },
          { data: { source: "segment:vector_db", target: "company:ExampleAI" } },
        ]);
        setHasMore(false);
      });
  };

  useEffect(() => {
    // Load initial graph
    load(true);
    // Load saved views
    try {
      const raw = localStorage.getItem("marketMapViews");
      if (raw) setViews(JSON.parse(raw));
    } catch {}
  }, []);

  // Infinite scroll: observe sentinel and load next page when visible
  useEffect(() => {
    if (!sentinelRef.current) return;
    const el = sentinelRef.current;
    const obs = new IntersectionObserver((entries) => {
      const entry = entries[0];
      if (entry.isIntersecting && hasMore) {
        load(false);
      }
    }, { root: null, rootMargin: '200px', threshold: 0 });
    obs.observe(el);
    return () => { try { obs.disconnect(); } catch {} };
  }, [hasMore, page, segment, minSignal]);

  const exportJson = async () => {
    const res = await axios.get(`${api}/market/export?format=json`);
    const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "market_map.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportPng = () => {
    try {
      const cy = cyRef.current;
      if (!cy) return;
      const uri = cy.png({ full: true, scale: 2, bg: "#ffffff" });
      const a = document.createElement("a");
      a.href = uri;
      a.download = "market_map.png";
      a.click();
    } catch {}
  };

  const persistViews = (v: View[]) => {
    setViews(v);
    try { localStorage.setItem("marketMapViews", JSON.stringify(v)); } catch {}
  };

  const saveView = () => {
    const name = prompt("Name this view:") || "";
    if (!name) return;
    try {
      const cy = cyRef.current;
      const pos: Record<string, any> = {};
      if (cy) {
        cy.nodes().forEach((n: any) => { pos[n.id()] = n.position(); });
      }
      const els = elements.map((el: any) => {
        if (el.data && el.data.id && pos[el.data.id]) {
          return { ...el, position: pos[el.data.id] };
        }
        return el;
      });
      const next = views.filter((v: View) => v.name !== name).concat([{ name, segment, minSignal, elements: els }]);
      persistViews(next);
      setSelectedView(name);
    } catch {}
  };

  const loadView = (name: string) => {
    setSelectedView(name);
    const v = views.find((x: View) => x.name === name);
    if (!v) return;
    setSegment(v.segment);
    setMinSignal(v.minSignal);
    // Use preset layout if positions exist
    setElements(v.elements || []);
    setTimeout(() => {
      const cy = cyRef.current;
      if (cy) {
        try { cy.layout({ name: "preset" }).run(); } catch {}
      }
    }, 0);
  };

  const deleteView = (name: string) => {
    const next = views.filter((v: View) => v.name !== name);
    persistViews(next);
    if (selectedView === name) setSelectedView("");
  };

  return (
    <div style={{ height: "80vh" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: 'center', flexWrap: 'wrap' }}>
  <input placeholder="Segment (e.g., Vector DB)" value={segment} onChange={(e: any) => setSegment(e.target.value)} style={{ border: "1px solid #ccc", padding: 6 }} />
  <input type="number" placeholder="Min signal" value={minSignal} onChange={(e: any) => setMinSignal(Number(e.target.value))} style={{ border: "1px solid #ccc", padding: 6, width: 120 }} />
        <button onClick={() => { setPage(1); load(true); }} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Apply</button>
        <button onClick={exportJson} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Export JSON</button>
        <button onClick={exportPng} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Export PNG</button>
  <a href={`${api}/market/export?format=csv`} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#fff", textDecoration: 'none' }}>Export CSV (Market)</a>
        <a href={`${api}/graph/export`} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#fff", textDecoration: 'none' }}>Export CSV (Graph)</a>
        {total !== null && (
          <span style={{ marginLeft: 8, color: '#555' }}>Loaded ~{elements.filter((e:any)=>!!e?.data?.id).length} of {total} companies</span>
        )}
        {hasMore && (
          <button onClick={() => load(false)} style={{ marginLeft: 'auto', padding: "6px 10px", border: "1px solid #ddd", background: "#eef6ff" }}>Load more</button>
        )}
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <select value={selectedView} onChange={(e: any) => loadView(e.target.value)} style={{ border: '1px solid #ddd', padding: 6 }}>
            <option value="">Saved views…</option>
            {views.map((v: View) => (
              <option key={v.name} value={v.name}>{v.name}</option>
            ))}
          </select>
          <button onClick={saveView} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Save View</button>
          {selectedView && (
            <button onClick={() => deleteView(selectedView)} style={{ padding: "6px 10px", border: "1px solid #fbb", background: "#fff0f0" }}>Delete</button>
          )}
        </div>
      </div>
  <CytoscapeComponent
        cy={(cy: any) => { cyRef.current = cy; }}
        elements={elements}
  layout={{ name: (elements.some((e:any)=>!!e.position) ? "preset" : "cose") as any }}
        stylesheet={[
          { selector: 'node', style: { 'label': 'data(label)', 'font-size': 10, 'text-valign': 'center', 'text-halign': 'center' } },
          { selector: 'node[type = "Company"]', style: { 'background-color': '#4f46e5', 'width': 'mapData(signal, 0, 100, 20, 60)', 'height': 'mapData(signal, 0, 100, 20, 60)' } },
          { selector: 'node[type = "Segment"]', style: { 'background-color': '#059669', 'shape': 'round-rectangle', 'width': 80, 'height': 30 } },
          { selector: 'edge', style: { 'line-color': '#ccc', 'target-arrow-color': '#ccc', 'target-arrow-shape': 'triangle' } }
        ]}
        style={{ width: "100%", height: "100%" }}
      />
  {/* sentinel for infinite scroll */}
  <div ref={sentinelRef} style={{ height: 1 }} />
    </div>
  );
}
