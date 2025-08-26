"use client";
import React, { useEffect, useState } from "react";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Jobs() {
  const [health, setHealth] = useState(null as any);
  const [status, setStatus] = useState(null as any);
  const load = async () => {
    try {
      const [h, s] = await Promise.all([
        fetch(`${api}/jobs/health`).then((r) => r.json()),
        fetch(`${api}/jobs/status`).then((r) => r.json()),
      ]);
      setHealth(h);
      setStatus(s);
    } catch {
      // ignore
    }
  };
  useEffect(() => {
    load();
  }, []);
  return (
    <main style={{ padding: 24 }}>
      <h1>Jobs & Health</h1>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={load}>Refresh</button>
      </div>
      <section style={{ marginTop: 16 }}>
        <h3>Backends</h3>
        <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(health?.backends || {}, null, 2)}</pre>
      </section>
      <section style={{ marginTop: 16 }}>
        <h3>Caches</h3>
        <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(health?.caches || {}, null, 2)}</pre>
      </section>
      <section style={{ marginTop: 16 }}>
        <h3>Evals</h3>
        <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(health?.evals || {}, null, 2)}</pre>
      </section>
      <section style={{ marginTop: 16 }}>
        <h3>Flows</h3>
        <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(status?.flows || [], null, 2)}</pre>
      </section>
    </main>
  );
}
