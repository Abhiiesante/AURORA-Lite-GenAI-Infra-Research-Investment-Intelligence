"use client";
export const dynamic = "force-dynamic";
import axios from "axios";
import { useEffect, useState } from "react";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Trends() {
  const [topics, setTopics] = useState([] as any[]);
  const [active, setActive] = useState(null as any);
  const [series, setSeries] = useState([] as any[]);
  useEffect(() => {
    axios.get(`${api}/trends/top?window=90d&limit=10`).then((res:any) => setTopics(res.data.topics || [])).catch(()=>setTopics([]));
  }, []);
  const selectTopic = async (t: any) => {
    setActive(t);
    try {
      const res:any = await axios.get(`${api}/trends/${t.topic_id}?window=90d`);
      setSeries(res.data.series || []);
    } catch {
      setSeries([]);
    }
  };
  return (
    <main style={{ padding: 24 }}>
      <h1>Trend Explorer</h1>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
  {topics.map((t:any) => (
          <button key={t.topic_id} onClick={() => selectTopic(t)} style={{ padding: 6, borderRadius: 6, border: '1px solid #ddd' }}>
            {t.label || `Topic ${t.topic_id}`}
          </button>
        ))}
      </div>
      {active && (
        <section style={{ marginTop: 16 }}>
          <h3>{active.label}</h3>
          <p>Top terms: {(active.terms || []).join(', ')}</p>
          <div>
            <strong>Weekly frequency</strong>
            <ul>
              {(series || []).map((p: any) => (
                <li key={p.date}>{p.date}: {p.value}</li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </main>
  );
}
