"use client";
export const dynamic = "force-dynamic";
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Weights = {
  growth_rate?: number;
  repo_stars_30d?: number;
  news_volume_z?: number;
  hiring_rate_30d?: number;
  patent_count_90d?: number;
};

type Config = {
  weights: Weights;
  alpha: number;
  delta_threshold: number;
};

const DEFAULTS: Config = {
  weights: {
    growth_rate: 0.5,
    repo_stars_30d: 0.2,
    news_volume_z: 0.3,
    hiring_rate_30d: 0,
    patent_count_90d: 0,
  },
  alpha: 0.3,
  delta_threshold: 1.8,
};

export default function SignalConfigPage() {
  const [cfg, setCfg] = useState(DEFAULTS as Config);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null as string | null);

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${api}/signals/config`);
        const data = r.data || {};
        setCfg({
          weights: { ...DEFAULTS.weights, ...(data.weights || {}) },
          alpha: typeof data.alpha === 'number' ? data.alpha : DEFAULTS.alpha,
          delta_threshold: typeof data.delta_threshold === 'number' ? data.delta_threshold : DEFAULTS.delta_threshold,
        });
      } catch {
        setCfg(DEFAULTS);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const setWeight = (k: keyof Weights, v: number) => setCfg((c: Config) => ({ ...c, weights: { ...c.weights, [k]: v } }));

  const totalWeight = useMemo(() => {
    const w = cfg.weights || {};
    return Object.values(w).reduce((s: number, x: unknown) => s + (typeof x === 'number' ? x : 0), 0);
  }, [cfg]);

  const save = async () => {
    setSaving(true); setMsg(null);
    try {
      await axios.put(`${api}/signals/config`, cfg);
      setMsg("Saved");
    } catch (e: any) {
      setMsg(e?.message || "Failed to save");
    } finally {
      setSaving(false);
      setTimeout(() => setMsg(null), 2000);
    }
  };

  const reset = () => setCfg(DEFAULTS);

  if (loading) return <div style={{ padding: 16 }}>Loading…</div>;

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <h2 style={{ marginTop: 0 }}>Signal Configuration</h2>
      <p style={{ color: '#555' }}>Tune weights, smoothing (alpha), and alert threshold. Changes take effect immediately for new computations.</p>

      <section style={{ border: '1px solid #eee', borderRadius: 8, padding: 12, marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>Weights</h3>
    {(Object.entries(cfg.weights) as [keyof Weights, number | undefined][]).map(([k, v]) => (
          <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '8px 0' }}>
            <label style={{ width: 180 }}>{k}</label>
      <input type="range" min={0} max={1} step={0.05} value={Number(v ?? 0)}
                   onChange={e => setWeight(k as keyof Weights, parseFloat(e.target.value))} style={{ flex: 1 }}/>
      <input type="number" min={0} max={1} step={0.05} value={Number(v ?? 0)}
                   onChange={e => setWeight(k as keyof Weights, parseFloat(e.target.value || '0'))} style={{ width: 90 }}/>
          </div>
        ))}
        <div style={{ fontSize: 12, color: totalWeight === 1 ? '#166534' : '#92400E' }}>Sum of weights: {totalWeight.toFixed(2)} {totalWeight !== 1 && '(tip: normalize to 1.00)'}</div>
      </section>

      <section style={{ border: '1px solid #eee', borderRadius: 8, padding: 12, marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>Smoothing and Threshold</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '8px 0' }}>
          <label style={{ width: 180 }}>alpha (EMA smoothing)</label>
     <input type="range" min={0.05} max={0.95} step={0.05} value={cfg.alpha}
       onChange={e => setCfg((c: Config) => ({ ...c, alpha: parseFloat(e.target.value) }))} style={{ flex: 1 }}/>
     <input type="number" min={0.05} max={0.95} step={0.05} value={cfg.alpha}
       onChange={e => setCfg((c: Config) => ({ ...c, alpha: parseFloat(e.target.value || '0.3') }))} style={{ width: 90 }}/>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '8px 0' }}>
          <label style={{ width: 180 }}>delta_threshold (z-score)</label>
     <input type="range" min={0.5} max={3} step={0.1} value={cfg.delta_threshold}
       onChange={e => setCfg((c: Config) => ({ ...c, delta_threshold: parseFloat(e.target.value) }))} style={{ flex: 1 }}/>
     <input type="number" min={0.5} max={3} step={0.1} value={cfg.delta_threshold}
       onChange={e => setCfg((c: Config) => ({ ...c, delta_threshold: parseFloat(e.target.value || '1.8') }))} style={{ width: 90 }}/>
        </div>
      </section>

      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={save} disabled={saving} style={{ padding: '8px 12px' }}>{saving ? 'Saving…' : 'Save'}</button>
        <button onClick={reset} style={{ padding: '8px 12px' }}>Reset</button>
        {msg && <span style={{ alignSelf: 'center', color: '#374151' }}>{msg}</span>}
      </div>

      <div style={{ marginTop: 16 }}>
        <a href="/alerts" style={{ fontSize: 13, padding: '6px 10px', border: '1px solid #ddd', borderRadius: 6, background: '#fff' }}>Back to Alerts</a>
      </div>
    </div>
  );
}
