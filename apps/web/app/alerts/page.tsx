"use client";
export const dynamic = "force-dynamic";
import { useEffect, useState } from "react";
import axios from "axios";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type AlertItem = { alert_id?: string|number; type: string; company_id?: number|string; created_at?: string; confidence?: number|null; evidence: string[]; explanation?: string|null };

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([] as AlertItem[]);
  const [hover, setHover] = useState(null as null | {url: string, title: string});

  useEffect(() => {
  axios.get(`${api}/alerts`).then((res: any) => setAlerts(res.data.alerts || [])).catch(() => setAlerts([]));
  }, []);

  const grouped = alerts.reduce((acc: Record<string, AlertItem[]>, a: any) => {
    (acc[a.type] = acc[a.type] || []).push(a);
    return acc;
  }, {});

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
      <h2>Alerts</h2>
      {Object.keys(grouped).map((t) => (
        <div key={t} style={{ marginTop: 16 }}>
          <h3>{t}</h3>
          <ul>
            {(grouped[t] || []).map((a: AlertItem, idx: number) => (
              <li key={idx} style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 12, color: '#666' }}>{a.created_at || ''}</div>
                <div>{a.explanation || ''}</div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {(a.evidence || []).map((u: string, i: number) => (
                    <button key={i} onMouseEnter={() => showTooltip(u)} style={{ border: '1px solid #ddd', background: '#f9f9f9', padding: '2px 6px' }}>Evidence {i+1}</button>
                  ))}
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
