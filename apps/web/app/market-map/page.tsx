"use client";
/// <reference path="../../types/shims.d.ts" />
import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import cytoscape from "cytoscape";
const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MarketMap() {
  type View = { name: string; segment: string; minSignal: number; elements: any[]; useKG?: boolean };
  const [elements, setElements] = useState([] as any[]);
  const [segment, setSegment] = useState("");
  const [minSignal, setMinSignal] = useState(0);
  const [page, setPage] = useState(1);
  const [size] = useState(200);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(null as number | null);
  const [views, setViews] = useState([] as View[]);
  const [selectedView, setSelectedView] = useState("");
  const [useKG, setUseKG] = useState(false);
  const [urlFiltersActive, setUrlFiltersActive] = useState(false);
  const cyRef = useRef(null as any);
  const sentinelRef = useRef(null as any);

  const toKey = (el: any) => {
    if (el?.data?.id) return `n:${el.data.id}`;
    if (el?.data?.source && el?.data?.target) return `e:${el.data.source}->${el.data.target}`;
    return Math.random().toString(36);
  };

  const load = (reset: boolean = false, forceUseKG?: boolean) => {
    const params = new URLSearchParams();
    if (segment) params.set("segment", segment);
    if (minSignal) params.set("min_signal", String(minSignal));
    params.set("page", String(reset ? 1 : page));
    params.set("size", String(size));
    const useKgFlag = typeof forceUseKG === 'boolean' ? forceUseKG : useKG;
    if (useKgFlag) params.set("source", "kg");
    axios.get(`${api}/market/realtime?${params.toString()}`)
      .then((res: any) => {
        const { nodes = [], edges = [], pagination } = res.data || {};
        // If API returns an empty graph, show a small example so the page isn't blank locally
        if ((!nodes || nodes.length === 0) && (!edges || edges.length === 0)) {
          setElements([
            { data: { id: "segment:vector_db", label: "Vector DB", type: "Segment" } },
            { data: { id: "company:ExampleAI", label: "ExampleAI", type: "Company", signal: 42 } },
            { data: { source: "segment:vector_db", target: "company:ExampleAI" } },
          ]);
          setHasMore(false);
          setTotal(1);
          if (reset) setPage(2);
          return;
        }
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

  // Apply filters helper used by Enter key and Apply button
  const applyFilters = () => {
    setPage(1);
    // reflect filters in URL
    try {
      const qs = new URLSearchParams(window.location.search || "");
      if (segment) qs.set('segment', segment); else qs.delete('segment');
      if (minSignal) qs.set('min_signal', String(minSignal)); else qs.delete('min_signal');
      if (useKG) qs.set('source','kg'); else qs.delete('source');
      const url = `${window.location.pathname}?${qs.toString()}`;
      window.history.replaceState(null, "", url);
    } catch {}
    load(true);
  };

  useEffect(() => {
    // Load URL params, saved views and KG preference, then initial graph using the preference
    let kgPref = false;
    try {
      const qs = new URLSearchParams(window.location.search || "");
      const seg = qs.get("segment");
      const ms = qs.get("min_signal");
      const src = qs.get("source");
      if (seg) setSegment(seg);
      if (ms) setMinSignal(Number(ms) || 0);
      if (src === 'kg') kgPref = true;
      setUrlFiltersActive(!!(seg || ms || src));
      const raw = localStorage.getItem("marketMapViews");
      if (raw) setViews(JSON.parse(raw));
      const kg = localStorage.getItem("marketMapUseKG");
      if (!kgPref && kg) kgPref = (kg === "1");
    } catch {}
    setUseKG(kgPref);
    load(true, kgPref);
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

  const toggleKG = () => {
    const next = !useKG;
    setUseKG(next);
    try { localStorage.setItem("marketMapUseKG", next ? "1" : "0"); } catch {}
    setPage(1);
    load(true, next);
    // reflect in URL
    try {
      const qs = new URLSearchParams(window.location.search || "");
      if (next) qs.set('source','kg'); else qs.delete('source');
      const url = `${window.location.pathname}?${qs.toString()}`;
      window.history.replaceState(null, "", url);
    } catch {}
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
      const next = views.filter((v: View) => v.name !== name).concat([{ name, segment, minSignal, elements: els, useKG }]);
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
    if (typeof v.useKG === 'boolean') setUseKG(v.useKG);
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

  // Minimal Cytoscape wrapper (avoids react-cytoscapejs runtime issues)
  const Graph = ({ elements, stylesheet }: { elements: any[]; stylesheet: any[] }) => {
  const containerRef = useRef(null as any);

    // init once
    useEffect(() => {
      if (!containerRef.current) return;
      const cy = cytoscape({
        container: containerRef.current,
        elements: elements as any,
        style: stylesheet as any,
      });
      cyRef.current = cy;
      // initial layout
      try {
        const hasPreset = (elements || []).some((e: any) => !!e.position);
        cy.layout({ name: hasPreset ? "preset" : "cose" } as any).run();
      } catch {}
      return () => {
        try { cy.destroy(); } catch {}
        cyRef.current = null;
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // updates on elements/style
    useEffect(() => {
      const cy = cyRef.current;
      if (!cy) return;
      try {
        cy.elements().remove();
        if (elements && elements.length) cy.add(elements as any);
        const hasPreset = (elements || []).some((e: any) => !!e.position);
        cy.layout({ name: hasPreset ? "preset" : "cose" } as any).run();
      } catch {}
    }, [elements]);

    return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
  };

  return (
    <div style={{ height: "80vh" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: 'center', flexWrap: 'wrap' }}>
  <input placeholder="Segment (e.g., Vector DB)" value={segment} onChange={(e: any) => setSegment(e.target.value)} onKeyDown={(e:any)=>{ if(e.key==='Enter'){ applyFilters(); } }} style={{ border: "1px solid #ccc", padding: 6 }} />
  <input type="number" placeholder="Min signal" value={minSignal} onChange={(e: any) => setMinSignal(Number(e.target.value))} onKeyDown={(e:any)=>{ if(e.key==='Enter'){ applyFilters(); } }} style={{ border: "1px solid #ccc", padding: 6, width: 120 }} />
        <button onClick={applyFilters} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Apply</button>
        <button onClick={exportJson} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Export JSON</button>
        <button onClick={exportPng} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Export PNG</button>
  <a href={`${api}/market/export?format=csv`} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#fff", textDecoration: 'none' }}>Export CSV (Market)</a>
        <a href={`${api}/graph/export`} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#fff", textDecoration: 'none' }}>Export CSV (Graph)</a>
        <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginLeft: 8 }}>
          <input type="checkbox" checked={useKG} onChange={toggleKG} /> Use KG source
        </label>
        {useKG && (
          <span style={{ padding: '2px 6px', background: '#eef6ff', border: '1px solid #bcd6ff', color: '#1d4ed8', borderRadius: 4 }}>
            KG mode
          </span>
        )}
        {total !== null && (
          <span style={{ marginLeft: 8, color: '#555' }}>Loaded ~{elements.filter((e:any)=>!!e?.data?.id).length} of {total} companies</span>
        )}
        {urlFiltersActive && (
          <span style={{ marginLeft: 8, color: '#6b7280' }} title="Filters derived from URL are applied">URL filters active</span>
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
          <a href="/kg" style={{ marginLeft: 6, padding: "6px 10px", border: "1px solid #ddd", background: "#fff", textDecoration: 'none' }}>Open KG Explorer</a>
          <button onClick={async () => {
            try {
              const qs = new URLSearchParams(window.location.search || "");
              if (segment) qs.set('segment', segment); else qs.delete('segment');
              if (minSignal) qs.set('min_signal', String(minSignal)); else qs.delete('min_signal');
              if (useKG) qs.set('source','kg'); else qs.delete('source');
              const url = `${window.location.origin}${window.location.pathname}${qs.toString() ? ('?' + qs.toString()) : ''}`;
              if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(url);
              } else {
                const ta = document.createElement('textarea');
                ta.value = url; document.body.appendChild(ta); ta.select();
                document.execCommand('copy'); document.body.removeChild(ta);
              }
              alert('Link copied to clipboard');
            } catch { alert('Copy failed'); }
          }} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#fff" }}>Copy Link</button>
          <button onClick={() => {
            // clear filters and URL
            setSegment("");
            setMinSignal(0);
            setUseKG(false);
            setSelectedView("");
            setPage(1);
            try {
              const url = window.location.pathname;
              window.history.replaceState(null, "", url);
            } catch {}
            load(true, false);
            setUrlFiltersActive(false);
          }} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#fff" }}>Reset</button>
        </div>
      </div>
      <Graph
        elements={elements}
        stylesheet={[
          { selector: 'node', style: { 'label': 'data(label)', 'font-size': 10, 'text-valign': 'center', 'text-halign': 'center' } },
          { selector: 'node[type = "Company"]', style: { 'background-color': '#4f46e5', 'width': 'mapData(signal, 0, 100, 20, 60)', 'height': 'mapData(signal, 0, 100, 20, 60)' } },
          { selector: 'node[type = "Segment"]', style: { 'background-color': '#059669', 'shape': 'round-rectangle', 'width': 80, 'height': 30 } },
          { selector: 'edge', style: { 'line-color': '#ccc', 'target-arrow-color': '#ccc', 'target-arrow-shape': 'triangle' } }
        ]}
      />
  {/* sentinel for infinite scroll */}
  <div ref={sentinelRef} style={{ height: 1 }} />
    </div>
  );
}
