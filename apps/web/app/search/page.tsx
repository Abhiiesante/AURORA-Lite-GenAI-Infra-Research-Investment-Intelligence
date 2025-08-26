"use client";
import { useState } from "react";
import axios from "axios";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState([] as any[]);
  const run = async () => {
    const { data } = await axios.get(`${api}/search`, { params: { q, limit: 10 } });
    setHits(data.hits || []);
  };
  return (
    <main style={{ padding: 24 }}>
      <h1>Search</h1>
      <input value={q} onChange={(e:any)=>setQ(e.target.value)} placeholder="Search companies" />
      <button onClick={run} disabled={!q.trim()}>Go</button>
      <ul>
        {hits.map((h:any)=>(
          <li key={h.id || h.url}><a href={`/companies/${h.id || ''}`}>{h.canonical_name || h.title || h.url}</a></li>
        ))}
      </ul>
    </main>
  );
}
