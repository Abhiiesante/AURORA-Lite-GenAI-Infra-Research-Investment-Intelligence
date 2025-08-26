"use client";
export const dynamic = "force-dynamic";
import dyn from "next/dynamic";
import { useState } from "react";
import axios from "axios";

const Plot = dyn(() => import("react-plotly.js"), { ssr: false } as any) as any;
const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ForecastPage() {
  const [companyId, setCompanyId] = useState(1);
  const [data, setData] = useState(null as any);
  const [shock, setShock] = useState("");

  const run = async () => {
    const r = await axios.post(`${api}/forecast/run`, { company_id: companyId, horizon_weeks: 12 });
    setData(r.data);
  };
  const whatif = async () => {
    if (!data) return;
    const r = await axios.post(`${api}/forecast/whatif`, { company_id: companyId, shock });
    setData(r.data);
  };

  const traces = data ? ([
    { x: Array.from({ length: (data.median || []).length }, (_, i) => i + 1), y: data.median, type: 'scatter', name: 'Median' },
    { x: Array.from({ length: (data.median || []).length }, (_, i) => i + 1), y: data.ci80, type: 'scatter', name: 'CI-80 Lo', line: { dash: 'dot' } },
    { x: Array.from({ length: (data.median || []).length }, (_, i) => i + 1), y: data.ci80_hi, type: 'scatter', name: 'CI-80 Hi', line: { dash: 'dot' } }
  ]) : [];

  return (
    <div style={{ padding: 16 }}>
      <h2>Forecast</h2>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <input type="number" value={companyId} onChange={(e: any) => setCompanyId(Number(e.target.value))} style={{ border: '1px solid #ccc', padding: 6, width: 120 }} />
        <button onClick={run} style={{ padding: '6px 10px', border: '1px solid #ddd', background: '#f5f5f5' }}>Run</button>
        <input placeholder="Shock (e.g., nvidia_price_drop_10pct)" value={shock} onChange={(e: any) => setShock(e.target.value)} style={{ border: '1px solid #ccc', padding: 6, minWidth: 280 }} />
        <button onClick={whatif} style={{ padding: '6px 10px', border: '1px solid #ddd', background: '#f5f5f5' }}>What-if</button>
      </div>
      {data && (
        <Plot data={traces} layout={{ title: `Company #${companyId} Forecast`, height: 420, margin: { t: 40 } }} />
      )}
    </div>
  );
}
