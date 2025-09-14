"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWithETag } from "../providers";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function Stat({ label, ok, details }: { label: string; ok: boolean; details?: any }) {
  return (
    <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 12, background: ok ? "#f0fff4" : "#fff5f5" }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      <div>Status: {ok ? "PASS" : "FAIL"}</div>
      {details && <div style={{ marginTop: 6, fontSize: 12, color: "#555" }}>{details}</div>}
    </div>
  );
}

export default function GateStatusPage() {
  const cache = React.useRef(new Map<string, any>());
  const { data, error, isLoading } = useQuery({
    queryKey: ["gate-status"],
    queryFn: async () => await fetchWithETag(`${API_URL}/dev/gates/status`, { etagCache: cache.current }),
    refetchInterval: 15000,
  });

  if (isLoading) return <div style={{ padding: 16 }}>Loading…</div>;
  if (error) return <div style={{ padding: 16, color: "#c00" }}>Failed to load gate status</div>;

  const perf = data?.perf || {};
  const forecast = data?.forecast || {};
  const errors = data?.errors || {};
  const rag = data?.rag || {};
  const market = data?.market || {};
  const evals = data?.evals || {};
  const overall = !!data?.pass;

  return (
    <div style={{ padding: 16 }}>
      <h1>Gate Status</h1>
      <div style={{ margin: "12px 0", fontWeight: 600 }}>Overall: {overall ? "PASS" : "FAIL"}</div>
      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
        <Stat label="Perf" ok={!!perf.pass} details={`p95=${perf.p95_ms}ms / budget=${perf.budget_ms}ms`} />
        <Stat label="Forecast" ok={!!forecast.pass} details={`SMAPE=${forecast.smape} / thr=${forecast.threshold}`} />
        <Stat label="Errors" ok={!!errors.pass} details={`rate=${errors.rate} / thr=${errors.threshold}`} />
        <Stat label="RAG" ok={!!rag.pass} details={`allowed=[${(rag.allowed||[]).join(', ')}]`} />
  <Stat label="Market" ok={!!market.pass} details={`p95=${market.p95_ms}ms / budget=${market.budget_ms}ms / size=${market.size}`} />
        {evals && typeof evals === 'object' && (
          <Stat label="Evals" ok={!!evals.pass} details={`F=${evals.faithfulness} / R=${evals.relevancy} / Rc=${evals.recall}`} />
        )}
      </div>
      <div style={{ marginTop: 16, fontSize: 12, color: "#666" }}>
        Auto-refreshes every 15s. Configure thresholds with environment variables in CI.
      </div>
    </div>
  );
}
