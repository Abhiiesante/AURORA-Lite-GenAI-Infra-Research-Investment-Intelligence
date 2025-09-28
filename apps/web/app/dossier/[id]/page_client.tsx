"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
import dynamic from "next/dynamic";
import { sfx } from "../../sfx";
import { TimeSeriesStack } from "../TimeSeriesStack";
import { RepoPanel } from "../RepoPanel";
import { ForecastWidget } from "../ForecastWidget";
import { DossierMemoist } from "../DossierMemoist";
import { ProvenanceModal } from "../ProvenanceModal";

const CompanySlab = dynamic(() => import("../CompanySlab").then(m=>m.CompanySlab), { ssr:false });

function useDossierCompany(id?: string){
  return useQuery({
    queryKey: ["dossier", id],
    enabled: !!id,
    queryFn: async () => (await fetch(`/api/dossier/${id}`)).json(),
  });
}

export default function DossierClient(){
  const { id } = useParams() as any;
  const reduced = useReducedMotion();
  const { data: company, isLoading } = useDossierCompany(id);
  const [memoOpen, setMemoOpen] = useState(false);
  const [memo, setMemo] = useState(null as any);
  const [ariaStatus, setAriaStatus] = useState("idle");
  const slabApiRef = useRef(null as any);
  const [provOpen, setProvOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  useEffect(() => { if (memoOpen) sfx.open(); }, [memoOpen]);

  const genMemo = useMutation({
    mutationFn: async (payload: any) => (await fetch(`/api/memo/generate`, { method:"POST", body: JSON.stringify(payload)})).json(),
    onMutate(){ setAriaStatus("Generating memo…"); },
    onSuccess(data: any){ setMemo(data); setAriaStatus("Memo ready with provenance"); sfx.confirm(); },
    onError(){ setAriaStatus("Memo generation failed"); }
  });

  if (!id) return <div>Missing id</div>;
  return (
    <main style={{ background: "var(--dossier-bg)", minHeight: "100vh" }} aria-busy={isLoading}>
      <div className="container" style={{ paddingTop: 16 }}>
        {/* Header */}
        <section className="dossier-glass" style={{ padding: 16, display: "grid", gridTemplateColumns: "360px 1fr 200px", alignItems: "center", gap: 16 }}>
          <div>
            <CompanySlab logoUrl={company?.logo} signalScore={company?.signalScore} healthColor="#00F0FF" reducedMotion={reduced}
              onReady={(api: any)=>{ slabApiRef.current = api; }} />
          </div>
            <div>
              <h1 className="dossier-header-title" style={{ fontSize: 40, color: "var(--dossier-accent)", margin: 0 }}>{company?.thesis || "Company Thesis"}</h1>
              {company?.tagline && <p style={{ marginTop: 6, opacity: 0.9 }}>{company.tagline}</p>}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <div className="glass" style={{ padding: "6px 10px", borderRadius: 999 }}>Signal: <b>{company?.signalScore ?? "–"}</b></div>
                <div className="glass" style={{ padding: "6px 10px", borderRadius: 999 }}>Momentum: <b>↑</b></div>
                <div className="glass" style={{ padding: "6px 10px", borderRadius: 999 }}>Top risk: <b>competition</b></div>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "end", gap: 8 }}>
              <button onClick={()=> { setMemoOpen(true); genMemo.mutate({ companyId: id, template: "onepager" }); }}
                className="magnetic" style={{ padding: "10px 14px", borderRadius: 12, border: "1px solid rgba(255,255,255,0.18)", background: "rgba(0,240,255,0.18)", color: "#001015", fontWeight: 700 }}>Generate Memo</button>
              <button onClick={()=> setProvOpen(true)} style={{ fontSize: 12, opacity: 0.8, background: "transparent", border: "none", textDecoration: "underline", cursor: "pointer"}}>Provenance</button>
              <button onClick={()=> setHelpOpen(true)} style={{ fontSize: 12, opacity: 0.8, background: "transparent", border: "none", textDecoration: "underline", cursor: "pointer"}}>Help</button>
            </div>
        </section>
        {/* Body */}
        <section style={{ display: "grid", gridTemplateColumns: "minmax(420px, 1fr) 360px", gap: 16, marginTop: 16, alignItems: "start" }}>
          {/* Left */}
          <div className="col">
            <article className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Narrative</h2>
              <div style={{ marginTop: 8 }}>
                {Array.isArray(company?.narrative?.bullets) && company.narrative.bullets.length ? (
                  <ul>
                    {company.narrative.bullets.map((b: any, i: number)=> (
                      <li key={b.id || i}>{b.text}{b.sources?.[0]?.url && <> <a href={b.sources[0].url} target="_blank" rel="noreferrer">[source]</a></>}</li>
                    ))}
                  </ul>
                ) : <em style={{ opacity: 0.7 }}>No narrative data</em>}
              </div>
            </article>
            <article className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Time Series</h2>
              <div style={{ marginTop: 8 }}>
                <TimeSeriesStack revenue={company?.metrics?.revenue} commits={company?.metrics?.commits} jobs={company?.metrics?.jobs} />
              </div>
              <div className="row" style={{ gap: 8, marginTop: 8 }}>
                <button className="magnetic" onClick={()=> {
                  const svg = document.querySelector('svg[aria-label^="Time series"]') as SVGSVGElement | null;
                  if (svg){
                    const evt = new CustomEvent('ts-export', { bubbles: true }); svg.dispatchEvent(evt);
                  }
                }}>Export image</button>
                <button className="magnetic" onClick={()=> {
                  const svg = document.querySelector('svg[aria-label^="Time series"]') as SVGSVGElement | null;
                  if (svg){ const evt = new CustomEvent('ts-toggle-table', { bubbles: true }); svg.dispatchEvent(evt); }
                }}>Toggle data table</button>
                <button className="magnetic" onClick={()=> {
                  const rows = (company?.metrics?.revenue||[]).map((d:any)=> `${d.date},${d.value}`).join('\n');
                  const blob = new Blob([`date,value\n${rows}`], { type: 'text/csv' });
                  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `${id}-revenue.csv`; a.click();
                }}>Export CSV</button>
              </div>
            </article>
            <article className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Developer Signals</h2>
              <RepoPanel repos={company?.repos} onAddToMemo={(item)=> {
                if (!memo) return;
                const next = { ...memo, bullets: [...(memo.bullets||[]), { id: `z${Date.now()}`, text: item.title, sources: item.source? [item.source]: [] }] };
                setMemo(next);
              }} />
            </article>
            <article className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Forecast & What‑If</h2>
              <ForecastWidget />
            </article>
          </div>
          {/* Right */}
          <aside className="col">
            <section className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Company</h2>
              <ul style={{ fontSize: 12, lineHeight: 1.8 }}>
                <li>Name: {company?.name}</li>
                <li>ID: {company?.id}</li>
                <li>Headcount: ~120</li>
                <li>HQ: US</li>
              </ul>
            </section>
            <section className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Timeline</h2>
              <ul style={{ fontSize: 12, lineHeight: 1.8 }}>
                {company?.timeline?.map((e: any)=> (
                  <li key={e.id}>{e.date} — {e.title} <a href={e.sources?.[0]?.url} target="_blank" rel="noreferrer">[source]</a></li>
                ))}
              </ul>
              <div style={{ marginTop: 8 }}>
                <label htmlFor="asof" style={{ fontSize: 12, opacity: 0.8 }}>As of</label>
                <input id="asof" type="date" style={{ display:"block", marginTop: 4, padding:"6px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.16)", background:"rgba(255,255,255,0.06)", color:"var(--dossier-text)" }} />
              </div>
            </section>
            <section className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Provenance</h2>
              <div style={{ fontSize: 12, opacity: 0.9 }}>Evidence (click to audit)</div>
              <ul style={{ fontSize: 12, lineHeight: 1.8, marginTop: 6 }}>
                <li><a href="#">doc:edgar-8k-2024</a></li>
                <li><a href="#">doc:press-2024</a></li>
              </ul>
            </section>
            <section className="dossier-glass" style={{ padding: 16 }}>
              <h2 style={{ fontSize: 16, margin: 0 }}>Quick actions</h2>
              <div className="row">
                <button className="magnetic" style={{ padding:"8px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.14)", background: "transparent", color:"var(--dossier-text)" }}>Watchlist</button>
                <button className="magnetic" style={{ padding:"8px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.14)", background: "transparent", color:"var(--dossier-text)" }}>DD Checklist</button>
                <button className="magnetic" style={{ padding:"8px 12px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.14)", background: "transparent", color:"var(--dossier-text)" }}>Share</button>
              </div>
            </section>
          </aside>
        </section>
      </div>
      {/* aria-live for memo status */}
      <div aria-live="polite" className="sr-only">{ariaStatus}</div>
      {memoOpen && (
        <DossierMemoist companyId={id} onClose={()=> setMemoOpen(false)} onComplete={(m)=> setMemo(m)} />
      )}
      {provOpen && (
        <ProvenanceModal onClose={()=> setProvOpen(false)} bundle={memo?.provenance_bundle} />
      )}
      {helpOpen && (
        <HelpOverlay onClose={()=> setHelpOpen(false)} />
      )}
      {/* Keyboard shortcuts: C create memo, S snapshot */}
      <ShortcutBinder onCreate={()=> { setMemoOpen(true); genMemo.mutate({ companyId: id, template: "onepager" }); }}
        onSnapshot={()=> {
          const dataUrl = slabApiRef.current?.snapshot();
          if (dataUrl){
            const a = document.createElement('a'); a.href = dataUrl; a.download = `${id}-header.png`; a.click();
          }
        }} />
    </main>
  );
}

function MemoModal({ memo, loading, onClose }: { memo: any; loading: boolean; onClose: ()=>void }){
  return (
    <div role="dialog" aria-modal className="cmdk-overlay" onClick={onClose}>
      <div className="cmdk-panel" onClick={e=>e.stopPropagation()} style={{ gridTemplateColumns: "1fr" }}>
        <header className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Generated Memo</h3>
          <button onClick={onClose}>Close</button>
        </header>
        <div className="glass" style={{ padding: 12, minHeight: 180 }}>
          {loading && <div>Generating…</div>}
          {memo && (
            <div>
              <p><b>Thesis:</b> {memo.thesis}</p>
              <ul>
                {memo.bullets?.map((b:any)=> <li key={b.id}>{b.text} <small>({b.sources?.join(', ')})</small></li>)}
              </ul>
              <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, opacity: 0.8 }}>{JSON.stringify(memo.provenance_bundle, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ShortcutBinder({ onCreate, onSnapshot }: { onCreate: ()=>void; onSnapshot: ()=>void }){
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'c' || e.key === 'C'){ e.preventDefault(); onCreate(); }
      if (e.key === 's' || e.key === 'S'){ e.preventDefault(); onSnapshot(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onCreate, onSnapshot]);
  return null;
}

function HelpOverlay({ onClose }: { onClose: ()=>void }){
  return (
    <div role="dialog" aria-modal className="cmdk-overlay" onClick={onClose}>
      <div className="cmdk-panel" onClick={e=>e.stopPropagation()} style={{ gridTemplateColumns: "1fr" }}>
        <header className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Help & Shortcuts</h3>
          <button onClick={onClose}>Close</button>
        </header>
        <ul style={{ fontSize: 14, lineHeight: 1.8 }}>
          <li>C — Generate memo</li>
          <li>S — Snapshot header slab</li>
          <li>Time Series: use buttons to Export image, Toggle data table, Export CSV</li>
        </ul>
      </div>
    </div>
  );
}

function useReducedMotion(){
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(!!mql.matches);
    onChange();
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, []);
  return reduced;
}
