"use client";
import axios from "axios";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CompanyClient(){
  const { id } = useParams() as any;
  const { data } = useQuery({
    queryKey: ["company", id],
    queryFn: async () => (await axios.get(`${api}/companies/${id}`)).data,
    enabled: !!id,
  });
  if (!id) return <div>Missing id</div>;
  if (!data) return <div>Loading…</div>;
  return (
    <main style={{ padding: 24 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <h1 style={{ margin: 0 }}>{data.canonical_name}</h1>
        <small style={{ opacity: 0.6 }}>#{data.id}</small>
      </header>
      <section style={{ marginTop: 12 }}>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: 14, lineHeight: 1.8 }}>
          <li><strong>Website:</strong> <a href={data.website} target="_blank" rel="noreferrer">{data.website}</a></li>
          <li><strong>HQ:</strong> {data.hq_country || 'n/a'}</li>
          <li><strong>Segments:</strong> {data.segments || 'n/a'}</li>
          <li><strong>Funding Total:</strong> {data.funding_total ?? 'n/a'}</li>
        </ul>
      </section>
      <Insights id={id} name={data.canonical_name} />
      <p style={{ marginTop: 24 }}><a href="/companies">Back to list</a></p>
    </main>
  );
}

function Insights({ id, name }: { id: string; name: string }){
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null as any);
  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${api}/insights/company/${id}`);
      setResult(data);
    } catch (e:any) {
      setResult({ error: e?.message || String(e) });
    } finally {
      setLoading(false);
    }
  };
  return (
    <section style={{ marginTop: 24 }}>
      <button onClick={run} disabled={loading}>{loading ? 'Retrieving…' : `Generate Brief for ${name}`}</button>
      {result && (
        <pre style={{ whiteSpace: 'pre-wrap', marginTop: 12 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </section>
  );
}
