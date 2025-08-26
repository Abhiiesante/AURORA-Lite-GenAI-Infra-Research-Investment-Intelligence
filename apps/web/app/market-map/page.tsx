"use client";
/// <reference path="../../types/shims.d.ts" />
import dyn from "next/dynamic";
import React, { useEffect, useState } from "react";
import axios from "axios";

const CytoscapeComponent = dyn(() => import("react-cytoscapejs"), { ssr: false });
const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MarketMap() {
  const [elements, setElements] = useState([] as any[]);
  const [segment, setSegment] = useState("");
  const [minSignal, setMinSignal] = useState(0);

  const load = () => {
    const params = new URLSearchParams();
    if (segment) params.set("segment", segment);
    if (minSignal) params.set("min_signal", String(minSignal));
    axios.get(`${api}/market/realtime?${params.toString()}`)
      .then((res: any) => {
        const { nodes, edges } = res.data;
        setElements([
          ...nodes.map((n: any) => ({ data: { id: n.id, label: n.label, type: n.type, segment: n.segment, signal: n.signal_score || 0 } })),
          ...edges.map((e: any) => ({ data: { source: e.source, target: e.target } }))
        ]);
      })
      .catch(() => {
        setElements([
          { data: { id: "segment:vector_db", label: "Vector DB" } },
          { data: { id: "company:ExampleAI", label: "ExampleAI" } },
          { data: { source: "segment:vector_db", target: "company:ExampleAI" } },
        ]);
      });
  };

  useEffect(() => { load(); }, []);

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

  return (
    <div style={{ height: "80vh" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
  <input placeholder="Segment (e.g., Vector DB)" value={segment} onChange={(e: any) => setSegment(e.target.value)} style={{ border: "1px solid #ccc", padding: 6 }} />
  <input type="number" placeholder="Min signal" value={minSignal} onChange={(e: any) => setMinSignal(Number(e.target.value))} style={{ border: "1px solid #ccc", padding: 6, width: 120 }} />
        <button onClick={load} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Apply</button>
        <button onClick={exportJson} style={{ padding: "6px 10px", border: "1px solid #ddd", background: "#f5f5f5" }}>Export JSON</button>
      </div>
      <CytoscapeComponent
        elements={elements}
        layout={{ name: "cose" }}
        stylesheet={[
          { selector: 'node', style: { 'label': 'data(label)', 'font-size': 10, 'text-valign': 'center', 'text-halign': 'center' } },
          { selector: 'node[type = "Company"]', style: { 'background-color': '#4f46e5', 'width': 'mapData(signal, 0, 100, 20, 60)', 'height': 'mapData(signal, 0, 100, 20, 60)' } },
          { selector: 'node[type = "Segment"]', style: { 'background-color': '#059669', 'shape': 'round-rectangle', 'width': 80, 'height': 30 } },
          { selector: 'edge', style: { 'line-color': '#ccc', 'target-arrow-color': '#ccc', 'target-arrow-shape': 'triangle' } }
        ]}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
