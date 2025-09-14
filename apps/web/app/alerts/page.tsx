"use client";
export const dynamic = "force-dynamic";
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AlertItem = { alert_id?: string|number; type: string; company_id?: number|string; created_at?: string; confidence?: number|null; evidence: string[]; explanation?: string|null };

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([] as AlertItem[]);
  const [typeFilter, setTypeFilter] = useState("");
  const [minConfidence, setMinConfidence] = useState(0);
  const [hover, setHover] = useState(null as null | {url: string, title: string});

  useEffect(() => {
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter, minConfidence]);

  const load = async () => {
    try {
      const params: any = {};
      if (typeFilter) params.type = typeFilter;
      if (minConfidence) params.min_confidence = minConfidence;
      const res = await axios.get(`${api}/alerts`, { params });
      setAlerts(res.data.alerts || []);
    } catch { setAlerts([]); }
  };

  const grouped = useMemo(() => alerts.reduce((acc: Record<string, AlertItem[]>, a: any) => {
    (acc[a.type] = acc[a.type] || []).push(a);
    return acc;
  }, {}), [alerts]);

  const badgeStyle = (conf?: number|null) => {
    const c = typeof conf === 'number' ? conf : -1;
    const bg = c >= 0.75 ? '#DCFCE7' : c >= 0.5 ? '#FEF9C3' : '#F3F4F6';
    const color = c >= 0.75 ? '#166534' : c >= 0.5 ? '#92400E' : '#374151';
  const style: any = { background: bg, color, borderRadius: 12, padding: '2px 8px', fontSize: 12, fontWeight: 600 };
  return style;
  };

  const toHost = (url: string) => {
    try { return new URL(url).host.replace('www.', ''); } catch { return url; }
  };

  const showTooltip = async (url: string) => {
    try {
      const r = await axios.get(`${api}/tools/snippet`, { params: { url } });
      setHover({ url, title: r.data.title || url });
      setTimeout(() => setHover(null), 3000);
    } catch {
      setHover({ url, title: url });
      setTimeout(() => setHover(null), 2000);
    }
  };

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>Alerts</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <a href={`${api}/alerts/export?format=csv`} style={{ fontSize: 13, padding: '6px 10px', border: '1px solid #ddd', borderRadius: 6, background: '#fff' }}>Export CSV</a>
          <a href={`/settings/signal-config`} style={{ fontSize: 13, padding: '6px 10px', border: '1px solid #ddd', borderRadius: 6, background: '#fff' }}>Edit Config</a>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center' }}>
        <label>Type
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} style={{ marginLeft: 6 }}>
            <option value="">All</option>
            <option value="threshold_crossing">threshold_crossing</option>
            <option value="filing_spike">filing_spike</option>
            <option value="repo_spike">repo_spike</option>
            <option value="anomaly_signal">anomaly_signal</option>
          </select>
        </label>
        <label>Min confidence
          <input type="number" min={0} max={1} step={0.05} value={minConfidence}
                 onChange={e => setMinConfidence(parseFloat(e.target.value || '0'))}
                 style={{ width: 80, marginLeft: 6 }}/>
        </label>
        <button onClick={load}>Apply</button>
      </div>
      {Object.keys(grouped).map((t) => (
        <div key={t} style={{ marginTop: 16 }}>
          <h3>{t}</h3>
          <ul>
            {(grouped[t] || []).map((a: AlertItem, idx: number) => (
              <li key={idx} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ fontSize: 12, color: '#666' }}>{a.created_at || ''}</div>
                  <span style={badgeStyle(a.confidence)}>conf: {typeof a.confidence === 'number' ? a.confidence.toFixed(2) : '–'}</span>
                </div>
                <div style={{ marginTop: 4 }}>{a.explanation || ''}</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {(a.evidence || []).map((u: string, i: number) => (
                    <button key={i} onMouseEnter={() => showTooltip(u)} title={u} style={{ border: '1px solid #ddd', background: '#f9f9f9', padding: '2px 6px', borderRadius: 6 }}>{toHost(u)}</button>
                  ))}
                </div>
                <div style={{ marginTop: 6, display: 'flex', gap: 8 }}>
                  <button onClick={() => axios.post(`${api}/alerts/label`, { alert_id: a.alert_id, label: 'tp' })}>Mark TP</button>
                  <button onClick={() => axios.post(`${api}/alerts/label`, { alert_id: a.alert_id, label: 'fp' })}>Mark FP</button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
      {hover && (
        <div style={{ position: 'fixed', bottom: 16, right: 16, background: 'white', border: '1px solid #ddd', padding: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <div style={{ fontWeight: 600 }}>Citation</div>
          <div style={{ maxWidth: 320 }}>{hover.title}</div>
        </div>
      )}
    </div>
  );
}
