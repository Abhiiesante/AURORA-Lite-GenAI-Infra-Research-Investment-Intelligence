"use client";
// Allow static generation during STATIC_EXPORT builds; otherwise force dynamic.
export const dynamic = process.env.STATIC_EXPORT ? "auto" : "force-dynamic";
import dyn from "next/dynamic";
import { useEffect, useState } from "react";
import axios from "axios";

const CytoscapeComponent = dyn(() => import("react-cytoscapejs"), { ssr: false } as any) as any;
const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PeoplePage() {
  const [elements, setElements] = useState([] as any[]);
  const [companyId, setCompanyId] = useState(1);
  const load = async () => {
    const r = await axios.get(`${api}/people/graph/${companyId}`);
    const { nodes, edges } = r.data;
    setElements([
      ...nodes.map((n: any) => ({ data: { id: n.id, label: n.label, type: n.type } })),
      ...edges.map((e: any) => ({ data: { source: e.source, target: e.target } }))
    ]);
  };
  useEffect(() => { load(); }, []);
  return (
    <div style={{ padding: 16 }}>
      <h2>People Graph</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <input type="number" value={companyId} onChange={(e: any) => setCompanyId(Number(e.target.value))} style={{ border: '1px solid #ccc', padding: 6, width: 120 }} />
        <button onClick={load} style={{ padding: '6px 10px', border: '1px solid #ddd', background: '#f5f5f5' }}>Load</button>
      </div>
      <div style={{ height: '70vh' }}>
        <CytoscapeComponent elements={elements} layout={{ name: 'cose' }} style={{ width: '100%', height: '100%' }} />
      </div>
    </div>
  );
}
