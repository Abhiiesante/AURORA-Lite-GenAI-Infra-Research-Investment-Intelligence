"use client";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const { data } = useQuery({
    queryKey: ["companies"],
    queryFn: async () => (await axios.get(`${api}/companies`)).data,
  });

  return (
    <main style={{ padding: 24 }}>
      <h1>AURORA-Lite</h1>
      <p>GenAI Infra Research & Investment Intelligence</p>
      <div style={{ display: 'flex', gap: 12 }}>
  <a href="/market-map">Market Map</a>
  <a href="/trends">Trends</a>
  <a href="/compare">Compare</a>
  <a href="/dashboard">Dashboard</a>
  <a href="/palette">Command‑K</a>
  <a href="/jobs">Jobs</a>
  <a href="/gate-status">Gate Status</a>
        <button onClick={() => axios.post(`${api}/health/seed`).then(()=>alert('Seeded DB/search')).catch(()=>alert('Seed failed'))}>Seed</button>
        <button onClick={() => axios.post(`${api}/health/seed-rag`).then(()=>alert('Seeded RAG')).catch(()=>alert('RAG seed failed'))}>Seed RAG</button>
      </div>
      <h2>Companies</h2>
      <ul>
        {(data || []).map((c: any) => (
          <li key={c.id}>
            <a href={`/companies/${c.id}`}>{c.canonical_name}</a> — {Array.isArray(c.segments) ? c.segments.join(", ") : (c.segments || "")}
          </li>
        ))}
      </ul>
    </main>
  );
}
