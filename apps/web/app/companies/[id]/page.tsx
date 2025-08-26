"use client";
import axios from "axios";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CompanyDetails() {
  const params = useParams() as any;
  const id = params?.id;
  const { data } = useQuery({
    queryKey: ["company", id],
    queryFn: async () => (await axios.get(`${api}/companies/${id}`)).data,
    enabled: !!id,
  });
  if (!id) return <div>Missing id</div>;
  if (!data) return <div>Loading…</div>;
  return (
    <main style={{ padding: 24 }}>
      <h1>{data.canonical_name}</h1>
      <p>Website: <a href={data.website} target="_blank" rel="noreferrer">{data.website}</a></p>
      <p>HQ: {data.hq_country || "–"}</p>
      <p>Segments: {data.segments || "–"}</p>
      <p>Funding Total: {data.funding_total ?? "–"}</p>
      <div style={{ marginTop: 16 }}>
        <GenerateBrief id={id} name={data.canonical_name} />
      </div>
      <p style={{ marginTop: 24 }}><a href="/">Back</a></p>
    </main>
  );
}

function GenerateBrief({ id, name }: { id: string; name: string }) {
  const [loading, setLoading] = useState(false as any);
  const [result, setResult] = useState(null as any);
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${api}/insights/company/${id}`);
      setResult(data);
    } catch (e) {
      setResult({ error: String(e) });
    } finally {
      setLoading(false);
    }
  };
  return (
    <div>
      <button onClick={run} disabled={loading}>{loading ? "Generating…" : `Generate Brief for ${name}`}</button>
      {result && (
        <pre style={{ whiteSpace: "pre-wrap", marginTop: 12 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}
