"use client";
import React, { useEffect, useState } from "react";
import { fetchDrivers } from './data';

type Driver = { url: string; score?: number; retrieved_at?: string };
type CompanyImpact = { company_id: string; impact_score?: number };

export function DriversModal({ open, onClose, topicId }: { open: boolean; onClose: ()=>void; topicId?: string }){
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null as null | {
    top_sources: Driver[];
    top_companies: CompanyImpact[];
    provenance_bundle?: any;
  });

  useEffect(()=>{
    if (!open || !topicId) return;
    let cancelled = false;
    (async ()=>{
      setLoading(true);
      try {
        const json = await fetchDrivers(topicId);
        if (!cancelled){ setData({ top_sources: json.top_sources||[], top_companies: json.top_companies||[], provenance_bundle: json.provenance_bundle }); }
      } catch (_e){
        if (!cancelled){ setData({ top_sources: [], top_companies: [] }); }
      } finally { if (!cancelled) setLoading(false); }
    })();
    return ()=>{ cancelled = true; };
  }, [open, topicId]);

  useEffect(()=>{
    const onKey = (e: KeyboardEvent) => { if (open && e.key === 'Escape'){ e.preventDefault(); onClose(); } };
    window.addEventListener('keydown', onKey);
    return ()=> window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="drivers-title" className="glass" style={{ position:'fixed', inset:0, background:'rgba(5,7,10,0.6)', display:'grid', placeItems:'center', zIndex: 70 }}>
      <div className="glass" style={{ width: 720, maxWidth:'95vw', padding: 16, borderRadius: 10, border:'1px solid rgba(255,255,255,0.18)' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 10 }}>
          <div id="drivers-title" className="title-orbitron" style={{ fontSize: 18 }}>Drivers</div>
          <button onClick={onClose} aria-label="Close drivers" className="trend-label" style={{ background:'transparent', border:'1px solid rgba(255,255,255,0.2)', padding:'6px 8px', borderRadius: 6, color:'var(--starlight)' }}>Close</button>
        </div>
        {loading && <div className="trend-label" aria-live="polite" style={{ opacity: 0.8 }}>Loading…</div>}
        {!loading && (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap: 12 }}>
            <div>
              <div className="trend-label" style={{ opacity:0.8, marginBottom:6 }}>Top sources</div>
              <div style={{ display:'grid', gap:6 }}>
                {(data?.top_sources||[]).map((s: Driver, i: number)=> (
                  <a key={i} href={s.url} target="_blank" rel="noreferrer" style={{ color:'var(--aurora-cyan)', textDecoration:'none', fontSize: 13 }}>
                    {s.url}
                    {typeof s.score === 'number' && <span className="numeric-sg" style={{ marginLeft: 6, opacity: 0.8 }}>({Math.round(s.score*100)}%)</span>}
                  </a>
                ))}
                {(data?.top_sources?.length||0)===0 && <div className="trend-label" style={{ opacity:0.7 }}>No sources</div>}
              </div>
            </div>
            <div>
              <div className="trend-label" style={{ opacity:0.8, marginBottom:6 }}>Impacted companies</div>
              <div style={{ display:'grid', gap:6 }}>
                {(data?.top_companies||[]).map((c: CompanyImpact, i: number)=> (
                  <div key={i} className="glass" style={{ padding:8, borderRadius:8 }}>
                    <div className="trend-label">{c.company_id}</div>
                    {typeof c.impact_score === 'number' && <div className="numeric-sg" style={{ fontSize: 12, opacity:0.8 }}>Impact {Math.round(c.impact_score*100)}%</div>}
                  </div>
                ))}
                {(data?.top_companies?.length||0)===0 && <div className="trend-label" style={{ opacity:0.7 }}>No companies</div>}
              </div>
            </div>
          </div>
        )}
        {!!data?.provenance_bundle && (
          <div className="glass" style={{ marginTop: 12, padding: 10, borderRadius: 8, border:'1px solid rgba(255,255,255,0.16)' }}>
            <div className="trend-label" style={{ opacity:0.8, marginBottom:6 }}>Provenance</div>
            <pre style={{ whiteSpace:'pre-wrap', fontSize: 12, lineHeight: 1.4 }}>{JSON.stringify(data.provenance_bundle, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
