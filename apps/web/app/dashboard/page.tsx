"use client";
export const dynamic = "force-dynamic";
import axios from "axios";
import { useState } from "react";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const [id, setId] = useState("1");
  const [data, setData] = useState(null as any);
  const [explain, setExplain] = useState("");
  const run = async () => {
    const res = await fetch(`/api/dashboard?id=${encodeURIComponent(id)}&window=90d`, { cache: "no-store" });
    const j = await res.json();
    setData(j);
  };
  const explainChart = async () => {
    const { data } = await axios.get(`${api}/insights/company/${id}`);
    setExplain((data?.summary || "").toString());
  };
  return (
    <main style={{ padding: 24 }}>
      <h1>Company Dashboard</h1>
      <div style={{ display: 'flex', gap: 8 }}>
        <input value={id} onChange={(e:any)=>setId(e.target.value)} placeholder="Company id" />
        <button onClick={run}>Load</button>
        <button onClick={explainChart} disabled={!data}>Explain this chart</button>
      </div>
      {data && (
        <section style={{ marginTop: 16 }}>
          <h3>{data.company}</h3>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(data.kpis, null, 2)}</pre>
          <div>
            <strong>Sparklines</strong>
            <ul>
              {(data.sparklines||[]).map((s:any)=> (
                <li key={s.metric}>{s.metric}: {s.series.length} points</li>
              ))}
            </ul>
          </div>
          {explain && <p style={{ marginTop: 8 }}>Explanation: {explain}</p>}
        </section>
      )}
    </main>
  );
}
