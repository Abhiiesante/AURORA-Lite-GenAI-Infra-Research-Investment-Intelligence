"use client";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import axios from "axios";

const CytoscapeComponent = dynamic(() => import("react-cytoscapejs"), { ssr: false } as any) as any;
const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function InvestorsPage() {
  const [vc, setVc] = useState("a16z");
  const [profile, setProfile] = useState(null as any);
  const [elements, setElements] = useState([] as any[]);

  const load = async () => {
    const pf = await axios.get(`${api}/investors/profile/${vc}`);
    setProfile(pf.data);
    const syn = await axios.get(`${api}/investors/syndicates/${vc}`);
    const { nodes, edges } = syn.data;
    setElements([
      ...nodes.map((n: any) => ({ data: { id: n.id, label: n.id } })),
      ...edges.map((e: any) => ({ data: { source: e.source, target: e.target } }))
    ]);
  };

  useEffect(() => { load(); }, []);

  return (
    <div style={{ padding: 16 }}>
      <h2>Investor Playbook</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <input value={vc} onChange={(e: any) => setVc(e.target.value)} style={{ border: '1px solid #ccc', padding: 6 }} />
        <button onClick={load} style={{ padding: '6px 10px', border: '1px solid #ddd', background: '#f5f5f5' }}>Load</button>
      </div>
      {profile && (
        <div style={{ marginBottom: 16 }}>
          <div>Likely Targets: {(profile.likely_targets || []).map((t: any, i: number) => <span key={i} style={{ marginRight: 8 }}>{t.size}/{t.geo}/{t.tech}</span>)}</div>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            {Object.entries(profile.focus || {}).map(([k, v]: any) => (
              <div key={k} style={{ padding: 6, border: '1px solid #eee', background: '#f9f9f9' }}>{k}: {v as number}</div>
            ))}
          </div>
        </div>
      )}
      <div style={{ height: '60vh' }}>
        <CytoscapeComponent elements={elements} layout={{ name: 'cose' }} style={{ width: '100%', height: '100%' }} />
      </div>
    </div>
  );
}
