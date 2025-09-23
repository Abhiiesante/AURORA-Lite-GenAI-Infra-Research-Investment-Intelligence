"use client";
import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import gsap from "gsap";
import "./trends-tokens.css";
import { TrendGalaxy } from "./TrendGalaxy";
import { BottomTimeline } from "./BottomTimeline";
import { TopicDetailPanel } from "./TopicDetailPanel";
import { TopicSearch } from "./TopicSearch";
import { DriversModal } from "./DriversModal";
import { captureElementPNG } from "./capture";
import { exportTrendsSVG } from './exportSvg';
import { Howl } from 'howler';
import { fetchTopics, fetchSeries, fetchChangePoints, useTopicStream, TopicStreamEvent } from './data';
import { ambientSources, hoverSources, pingSources, snapshotSources } from './audio';

export default function TrendsPage(){
  const [topics, setTopics] = useState([] as any);
  const [selected, setSelected] = useState(null as any);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [markers, setMarkers] = useState([] as any);
  const [searchOpen, setSearchOpen] = useState(false);
  const [driversOpen, setDriversOpen] = useState(false);
  const [ariaMsg, setAriaMsg] = useState("");
  const heroRef = React.useRef(null as unknown as HTMLDivElement | null);
  const [compare, setCompare] = useState([] as any[]);
  const [compareMode, setCompareMode] = useState(false);
  // Lasso state (screen-space in hero)
  const [lasso, setLasso] = useState(null as null | { x0:number;y0:number;x1:number;y1:number });
  const [screenPts, setScreenPts] = useState([] as Array<{ x:number;y:number;id:string }>);
  const shiftDown = React.useRef(false);
  const ambient = React.useRef(null as unknown as Howl | null);
  const sHover = React.useRef(null as unknown as Howl | null);
  const sPing = React.useRef(null as unknown as Howl | null);
  const sSnap = React.useRef(null as unknown as Howl | null);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const duckTimer = React.useRef(null as unknown as number | null);
  const pendingMarkerAdds = React.useRef([] as any[]);
  const pendingMarkerRemoves = React.useRef([] as any[]);
  const markersFlushTimer = React.useRef(null as unknown as number | null);

  const baseAmbientVol = useMemo(()=> (muted? 0 : 0.06) * volume, [muted, volume]);
  const duckAmbient = (ms = 420, factor = 0.35) => {
    try{
      const ambientHowl = ambient.current;
      if (!ambientHowl) return;
      const target = baseAmbientVol * factor;
      ambientHowl.volume(Math.max(0, target));
      if (duckTimer.current) window.clearTimeout(duckTimer.current);
      duckTimer.current = window.setTimeout(()=>{
        try { ambientHowl.volume(baseAmbientVol); } catch {}
      }, ms);
    } catch {}
  };

  useEffect(() => { (async () => {
    const data = await fetchTopics({ window: '90d' });
    setTopics(data.topics || []);
    setMarkers((data.topics||[]).slice(0,6).map((_:any,i:number)=>({t: (i+1)/7, label: 'change-point'})));
  })(); }, []);

  useEffect(() => {
    const prefersReduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;
    let raf: number;
    const loop = () => {
      if (playing){ setTime((t: number) => (t + 0.003) % 1); }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  useEffect(()=>{
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase()==='k' && (e.ctrlKey || e.metaKey)){
        e.preventDefault(); setSearchOpen(true);
      }
  if (e.key===' '){ e.preventDefault(); setPlaying((p: boolean)=>!p); }
  if (e.key.toLowerCase()==='j'){ setTime((t: number)=> Math.max(0, t-0.02)); }
  if (e.key.toLowerCase()==='l'){ setTime((t: number)=> Math.min(1, t+0.02)); }
      if (e.key === 'Shift'){ shiftDown.current = true; }
    };
    window.addEventListener('keydown', onKey);
    const onKeyUp = (e: KeyboardEvent) => { if (e.key === 'Shift') shiftDown.current = false; };
    window.addEventListener('keyup', onKeyUp);
    return ()=> { window.removeEventListener('keydown', onKey); window.removeEventListener('keyup', onKeyUp); };
  }, []);

  // Sounds
  useEffect(()=>{
    // restore persisted audio prefs
    try {
      const m = localStorage.getItem('trends_audio_muted');
      const v = localStorage.getItem('trends_audio_volume');
      if (m != null) setMuted(m === '1');
      if (v != null) setVolume(Math.min(1, Math.max(0, parseFloat(v))));
    } catch {}
  }, []);

  useEffect(()=>{
    ambient.current = new Howl({ src: ambientSources, loop: true, volume: baseAmbientVol });
    sHover.current = new Howl({ src: hoverSources, volume: (muted? 0 : 0.2) * volume });
    sPing.current = new Howl({ src: pingSources, volume: (muted? 0 : 0.35) * volume });
    sSnap.current = new Howl({ src: snapshotSources, volume: (muted? 0 : 0.35) * volume });
    try { if (!muted) ambient.current?.play(); } catch {}
    return ()=> { ambient.current?.stop(); };
  }, [muted, volume, baseAmbientVol]);

  useEffect(()=>{
    // persist audio prefs
    try {
      localStorage.setItem('trends_audio_muted', muted ? '1' : '0');
      localStorage.setItem('trends_audio_volume', String(volume));
    } catch {}
  }, [muted, volume]);

  // Optional: live updates via WebSocket (enabled when NEXT_PUBLIC_WS_URL is defined)
  useTopicStream({ enabled: Boolean(process.env.NEXT_PUBLIC_WS_URL), url: process.env.NEXT_PUBLIC_WS_URL, onEvent: (e: TopicStreamEvent)=>{
    // Map selected/change_point events into UI
    if (e.type === 'change_point' && typeof e.date === 'string'){
      setMarkers((prev:any[])=>{
        const t = new Date(e.date as string).getTime();
        // We need series bounds to map to [0..1]; fall back to time modulo
        const frac = ((t/1000) % 86400) / 86400; // pseudo-position within a day
        const m = { t: frac, label: e.kind || 'change-point' };
        return [...prev.slice(-9), m];
      });
      setAriaMsg(`Live change-point at ${new Date(e.date).toLocaleDateString()}`);
      sPing.current?.play(); duckAmbient();
    }
    if (e.type === 'select' && e.topic_id){
      const t = (topics||[]).find((x:any)=> x.topic_id===e.topic_id);
      if (t) setSelected(t);
    }
    if (e.type === 'compare_add' && e.topic_id){
      const t = (topics||[]).find((x:any)=> x.topic_id===e.topic_id);
      if (t) setCompare((list:any[])=>[...list, t].slice(-3));
    }
    if (e.type === 'compare_remove' && e.topic_id){
      setCompare((list:any[])=> list.filter(x=> x.topic_id !== e.topic_id));
    }
    if (e.type === 'markers_set' && Array.isArray(e.items)){
      // Expect items: [{ t: number, label?: string }]
      const next = e.items
        .map((m:any)=> ({ t: Math.max(0, Math.min(1, Number(m.t) || 0)), label: typeof m.label==='string'? m.label : undefined }))
        .slice(0, 32);
      setMarkers(next);
      setAriaMsg(`Markers updated (${next.length})`);
    }
    // Debounced markers add/remove lifecycle
    const scheduleMarkersFlush = () => {
      if (markersFlushTimer.current) return;
      markersFlushTimer.current = window.setTimeout(()=>{
        setMarkers((prev:any[])=>{
          const eps = 0.01;
          let arr = prev.slice();
          // Removes first
          if (pendingMarkerRemoves.current.length){
            const rem = pendingMarkerRemoves.current.splice(0);
            arr = arr.filter(m=> !rem.some((r:any)=> (typeof r.t==='number' && Math.abs((r.t as number) - m.t) < eps) && (!r.label || r.label===m.label)));
          }
          // Adds next
          if (pendingMarkerAdds.current.length){
            const adds = pendingMarkerAdds.current.splice(0).map((m:any)=> ({ t: Math.max(0, Math.min(1, Number(m.t) || 0)), label: typeof m.label==='string'? m.label : undefined }));
            for (const a of adds){
              const dup = arr.some(m=> Math.abs(m.t - a.t) < eps && (m.label===a.label));
              if (!dup) arr.push(a);
            }
          }
          // Clamp size
          if (arr.length > 64) arr = arr.slice(-64);
          setAriaMsg(`Markers: ${arr.length}`);
          return arr;
        });
        if (markersFlushTimer.current){ window.clearTimeout(markersFlushTimer.current); markersFlushTimer.current = null; }
      }, 200);
    };
    if (e.type === 'markers_add' && Array.isArray(e.items)){
      pendingMarkerAdds.current.push(...e.items);
      scheduleMarkersFlush();
    }
    if (e.type === 'markers_remove' && Array.isArray(e.items)){
      pendingMarkerRemoves.current.push(...e.items);
      scheduleMarkersFlush();
    }
    // Lasso set/clear
    if (e.type === 'lasso_set' && e.rect){
      const host = heroRef.current as HTMLDivElement | null;
      const rect = host?.getBoundingClientRect();
      let { x0, y0, x1, y1 } = e.rect as any;
      if (e.units === 'normalized' && rect){
        x0 *= rect.width; x1 *= rect.width; y0 *= rect.height; y1 *= rect.height;
      }
      const l = { x0, y0, x1, y1 } as { x0:number;y0:number;x1:number;y1:number };
      setLasso(l);
      // Compute hits and optionally update selection/compare
      const rx0 = Math.min(l.x0, l.x1), ry0 = Math.min(l.y0, l.y1);
      const rx1 = Math.max(l.x0, l.x1), ry1 = Math.max(l.y0, l.y1);
      const hits = screenPts.filter((p: {x:number;y:number;id:string})=> p.x>=rx0 && p.x<=rx1 && p.y>=ry0 && p.y<=ry1);
      if (hits.length){
        const picked = hits.map((h: {id:string})=> topics.find((t:any)=> t.topic_id===h.id)).filter(Boolean) as any[];
        if (e.mode === 'compare'){
          setCompare((list:any[])=>{
            const add = picked.filter(p=> !list.find((x:any)=> x.topic_id===p.topic_id));
            return [...list, ...add].slice(-3);
          });
        } else if (e.mode === 'select'){
          setSelected(picked[0]);
        }
        setAriaMsg(`Lasso picked ${picked.length}`);
      }
    }
    if (e.type === 'lasso_clear'){
      setLasso(null);
      setAriaMsg('Lasso cleared');
    }
    // Timeline set
    if (e.type === 'timeline_set' && typeof e.t === 'number'){
      setTime(Math.max(0, Math.min(1, e.t as number)));
      if (typeof e.playing === 'boolean') setPlaying(!!e.playing);
      setAriaMsg(`Timeline set to ${(Math.max(0, Math.min(1, e.t as number))*100|0)}%`);
    }
  }});

  return (
    <div className="trends-bg" style={{ display:'grid', gridTemplateColumns:'280px 1fr 380px', gridTemplateRows:'60vh auto', gridTemplateAreas:`
      'hero hero hero'
      'left main right'
    `, gap: 16, padding: '16px 16px 60px' }}>
      {/* Hero */}
  <div style={{ gridArea:'hero', position:'relative' }} ref={heroRef}>
        <div style={{ position:'absolute', inset:0 }}>
          <TrendGalaxy topics={topics} time={time} markers={markers} onScreenPositions={(pts)=> setScreenPts(pts)} selectedId={selected?.topic_id || null} onTopicSelect={(id)=>{ const t = topics.find((x:any)=>x.topic_id===id); setSelected(t); }} />
        </div>
        {/* Lasso rect overlay */}
        {lasso && (
          <div className="glass" style={{ position:'absolute', left: Math.min(lasso.x0, lasso.x1), top: Math.min(lasso.y0, lasso.y1), width: Math.abs(lasso.x1 - lasso.x0), height: Math.abs(lasso.y1 - lasso.y0), border:'1px dashed rgba(0,240,255,0.8)', background:'rgba(0,240,255,0.08)', pointerEvents:'none' }} />
        )}
        {/* Mouse handlers for lasso */}
        <div style={{ position:'absolute', inset:0 }} onMouseDown={(e)=>{
          const r = (heroRef.current as HTMLDivElement).getBoundingClientRect();
          setLasso({ x0: e.clientX - r.left, y0: e.clientY - r.top, x1: e.clientX - r.left, y1: e.clientY - r.top });
        }} onMouseMove={(e)=>{
          if (!lasso) return;
          const r = (heroRef.current as HTMLDivElement).getBoundingClientRect();
          setLasso({ ...lasso, x1: e.clientX - r.left, y1: e.clientY - r.top });
        }} onMouseUp={()=>{
          if (!lasso) return;
          const x0 = Math.min(lasso.x0, lasso.x1), y0 = Math.min(lasso.y0, lasso.y1);
          const x1 = Math.max(lasso.x0, lasso.x1), y1 = Math.max(lasso.y0, lasso.y1);
          const hits = screenPts.filter((p: {x:number;y:number;id:string})=> p.x>=x0 && p.x<=x1 && p.y>=y0 && p.y<=y1);
          const picked = hits.map((h: {x:number;y:number;id:string})=> topics.find((t:any)=> t.topic_id === h.id)).filter(Boolean) as any[];
          if (picked.length){
            if (compareMode || shiftDown.current){
              setCompare((list: any[])=>{
                const add = picked.filter(p=> !list.find((x:any)=> x.topic_id===p.topic_id));
                return [...list, ...add].slice(-3);
              });
            } else {
              setSelected(picked[0]);
            }
          }
          setLasso(null);
        }} />
        {/* Overlays */}
        <div style={{ position:'absolute', top:16, left:16, right:16, display:'flex', justifyContent:'space-between', gap:12 }}>
          <div className="glass" style={{ padding:8, display:'flex', gap:8, alignItems:'center', flex:1 }}>
            <span className="title-orbitron" style={{ fontSize:18 }}>Explore Trends — Currents of Attention</span>
            <input onFocus={()=>setSearchOpen(true)} placeholder="Search topics (Cmd+K)" style={{ flex:1, background:'transparent', border:'none', color:'var(--starlight)', outline:'none', cursor:'pointer' }} readOnly />
          </div>
          <div className="glass" style={{ padding:8, display:'flex', gap:8, alignItems:'center' }}>
            <button className="trend-label" style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.16)', color:'var(--starlight)', borderRadius:6, padding:'8px 10px' }}>Sector</button>
            <button className="trend-label" style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.16)', color:'var(--starlight)', borderRadius:6, padding:'8px 10px' }}>Geo</button>
            <button className="trend-label" style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.16)', color:'var(--starlight)', borderRadius:6, padding:'8px 10px' }}>Window</button>
            <div style={{ width:1, height:24, background:'rgba(255,255,255,0.18)' }} />
            <button aria-label={muted? 'Unmute': 'Mute'} className="trend-label" onClick={()=> setMuted((m: boolean)=>!m)} style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.16)', color:'var(--starlight)', borderRadius:6, padding:'8px 10px' }}>{muted? '🔇' : '🔊'}</button>
            <input aria-label="Volume" type="range" min={0} max={1} step={0.05} value={volume} onChange={(e)=> setVolume(parseFloat(e.target.value))} style={{ width:120 }} />
          </div>
        </div>
        {/* FABs */}
        <div style={{ position:'absolute', right:16, bottom:16, display:'grid', gap:8 }}>
          <button className="glass" onClick={async ()=>{
            try {
              // Visual capture
              const host = heroRef.current || document.body;
              const dataUrl = await captureElementPNG(host as HTMLElement);
              // Download locally
              const a = document.createElement('a');
              a.href = dataUrl; a.download = `trends_snapshot_${Date.now()}.png`; a.click();
              sSnap.current?.play(); duckAmbient();
              // Persist metadata (mock API)
              const payload = { as_of: new Date().toISOString(), selected: selected? [selected.topic_id]: [], filters: {}, notes: "" };
              const res = await fetch('/api/topics/snapshot', { method:'POST', headers:{ 'content-type':'application/json' }, body: JSON.stringify(payload) });
              const json = await res.json();
              setAriaMsg(`Snapshot saved: ${json.snapshot_id}`);
            } catch (_e){ setAriaMsg('Snapshot failed'); }
          }} style={{ padding:'10px 12px', borderRadius:24, border:'1px solid rgba(255,255,255,0.18)' }}>Snapshot</button>
          <button className="glass" onClick={async ()=>{
            try{
              const host = heroRef.current || document.body;
              const dataUrl = await captureElementPNG(host as HTMLElement);
              const { jsPDF } = await import('jspdf');
              const pdf = new jsPDF({ orientation: 'landscape', unit: 'px', format: 'a4' });
              const pageW = pdf.internal.pageSize.getWidth();
              const pageH = pdf.internal.pageSize.getHeight();
              // Fit image within page with small margin
              const margin = 24;
              const imgW = pageW - margin*2;
              const imgH = pageH - margin*2;
              pdf.addImage(dataUrl, 'PNG', margin, margin, imgW, imgH, undefined, 'FAST');
              // Metadata footer
              pdf.setFontSize(10);
              pdf.text(`As of ${new Date().toLocaleString()} — Selected: ${selected? selected.label : 'None'}`, margin, pageH - 8);
              pdf.save('trends.pdf');
              setAriaMsg('PDF exported');
            } catch(_e){ setAriaMsg('PDF export failed'); }
          }} style={{ padding:'10px 12px', borderRadius:24, border:'1px solid rgba(255,255,255,0.18)' }}>Export PDF</button>
          <button className="glass" onClick={async ()=>{
            try{
              // Page 1: PNG of hero
              const host = heroRef.current || document.body;
              const dataUrl = await captureElementPNG(host as HTMLElement);
              // Page 2: rasterized SVG overlay
              const rect = (heroRef.current as HTMLDivElement | null)?.getBoundingClientRect();
              const points = screenPts
                .map((p: { x:number;y:number;id:string })=>{
                  const t = topics.find((x:any)=> x.topic_id===p.id);
                  return { ...p, label: t?.label, selected: selected?.topic_id === p.id, compare: !!compare.find((c:any)=> c.topic_id === p.id) };
                })
                .filter((p: { selected?: boolean; compare?: boolean })=> !!(p.selected || p.compare));
              const { width, height } = { width: rect?.width || 1200, height: rect?.height || 600 };
              // Build SVG string directly using utility
              const { buildSvgString } = await import('./svgString');
              const svgStr = buildSvgString({ width, height, points, lasso, markers, title: 'Explore Trends — Currents of Attention', asOf: new Date().toLocaleString() });
              // Convert SVG string to PNG for PDF embedding
              const svgBlob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
              const svgUrl = URL.createObjectURL(svgBlob);
              const img = new Image();
              const pngUrl: string = await new Promise((resolve, reject)=>{
                img.onload = () => {
                  try {
                    const c = document.createElement('canvas'); c.width = width; c.height = height;
                    const ctx = c.getContext('2d'); if (!ctx) throw new Error('no ctx');
                    ctx.drawImage(img, 0, 0);
                    resolve(c.toDataURL('image/png'));
                  } catch (err){ reject(err); }
                };
                img.onerror = reject;
                img.src = svgUrl;
              });
              URL.revokeObjectURL(svgUrl);

              const { jsPDF } = await import('jspdf');
              const pdf = new jsPDF({ orientation: 'landscape', unit: 'px', format: 'a4' });
              const pageW = pdf.internal.pageSize.getWidth();
              const pageH = pdf.internal.pageSize.getHeight();
              const margin = 24;
              const imgW = pageW - margin*2;
              const imgH = pageH - margin*2;
              pdf.addImage(dataUrl, 'PNG', margin, margin, imgW, imgH, undefined, 'FAST');
              pdf.text('Overlay (SVG)', margin, pageH - 8);
              pdf.addPage();
              pdf.addImage(pngUrl, 'PNG', margin, margin, imgW, imgH, undefined, 'FAST');
              pdf.text('Overlay (SVG rasterized)', margin, pageH - 8);
              pdf.save('trends_bundle.pdf');
              setAriaMsg('Bundle exported');
            } catch(_e){
              setAriaMsg('Bundle export failed');
            }
          }} style={{ padding:'10px 12px', borderRadius:24, border:'1px solid rgba(255,255,255,0.18)' }}>Export Bundle</button>
          <button className="glass" onClick={()=> setCompareMode((m: boolean)=>!m)} style={{ padding:'10px 12px', borderRadius:24, border:'1px solid rgba(255,255,255,0.18)', background: compareMode? 'rgba(0,240,255,0.12)':'transparent' }}>Compare</button>
          <button className="glass" onClick={()=>{
            try{
              const host = heroRef.current as HTMLDivElement | null;
              const rect = host?.getBoundingClientRect();
              const points = screenPts
                .map((p: { x:number;y:number;id:string })=>{
                  const t = topics.find((x:any)=> x.topic_id===p.id);
                  return {
                    ...p,
                    label: t?.label,
                    selected: selected?.topic_id === p.id,
                    compare: !!compare.find((c:any)=> c.topic_id === p.id)
                  };
                })
                .filter((p: { selected?: boolean; compare?: boolean })=> !!(p.selected || p.compare));
              exportTrendsSVG({
                width: rect?.width || 1200,
                height: rect?.height || 600,
                points,
                lasso,
                markers,
                title: 'Explore Trends — Currents of Attention',
                asOf: new Date().toLocaleString()
              });
              setAriaMsg('SVG export ready');
            } catch(_e){ setAriaMsg('SVG export failed'); }
          }} style={{ padding:'10px 12px', borderRadius:24, border:'1px solid rgba(255,255,255,0.18)' }}>Export SVG</button>
          <button className="glass" onClick={()=> {
            const sel = selected? [selected] : [];
            const payload = {
              as_of: new Date().toISOString(),
              selected: sel.map(s=>({ id: s.topic_id, label: s.label, momentum: s.momentum })),
              compare: compare.map((s: any)=>({ id: s.topic_id, label: s.label })),
              topics_count: topics.length
            };
            // Build CSV
            const headers = ['id','label','momentum'];
            const lines = [headers.join(',')].concat(sel.map(s=> [s.topic_id, JSON.stringify(s.label), String(s.momentum)].join(',')));
            const csv = lines.join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `export_${Date.now()}.csv`; a.click();
            // JSON bundle
            const jblob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
            const a2 = document.createElement('a'); a2.href = URL.createObjectURL(jblob); a2.download = `export_${Date.now()}.json`; a2.click();
            setAriaMsg('Export ready');
          }} style={{ padding:'10px 12px', borderRadius:24, border:'1px solid rgba(255,255,255,0.18)' }}>Export</button>
          <button className="glass" style={{ padding:'10px 12px', borderRadius:24, border:'1px solid rgba(255,255,255,0.18)', background:'rgba(0,240,255,0.12)' }}>Auto-Detect</button>
        </div>
        <div aria-live="polite" className="trend-label" style={{ position:'absolute', left:-99999, top:'auto', width:1, height:1, overflow:'hidden' }}>{ariaMsg}</div>
      </div>

      {/* Left rail */}
      <div style={{ gridArea:'left' }}>
        <div className="glass" style={{ padding:12, marginBottom:12 }}>
          <div className="trend-label" style={{ opacity:0.8, marginBottom:8 }}>Selected topics</div>
          <div style={{ display:'grid', gap:6 }}>
            {(selected?[selected]:[]).map((t:any)=>(
              <div key={t.topic_id} className="glass" style={{ padding:8, borderRadius:8 }}>{t?.label}</div>
            ))}
          </div>
        </div>
        <div className="glass" style={{ padding:12 }}>
          <div className="trend-label" style={{ opacity:0.8, marginBottom:8 }}>Quick filters</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
            {['AI','Infra','Security','DevTools','Healthcare'].map((f)=>(
              <button key={f} className="trend-label" style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.16)', color:'var(--starlight)', borderRadius:6, padding:'6px 8px' }}>{f}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Main list with compare selection */}
      <div style={{ gridArea:'main' }}>
        <div className="glass" style={{ padding:12 }}>
          <div className="trend-label" style={{ opacity:0.8, marginBottom:8 }}>Topics</div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(220px, 1fr))', gap:8 }}>
            {topics.slice(0,12).map((t:any)=>(
              <button key={t.topic_id} onClick={()=>{
                if (compareMode){
                  setCompare((list: any[])=>{
                    if (list.find((x: any)=>x.topic_id===t.topic_id)) return list.filter((x: any)=>x.topic_id!==t.topic_id);
                    return [...list, t].slice(-3);
                  });
                } else {
                  setSelected(t);
                }
                sHover.current?.play();
              }} className="glass" style={{ textAlign:'left', padding:10, borderRadius:8, cursor:'pointer', outline: compare.find((x:any)=>x.topic_id===t.topic_id)? '1px solid var(--aurora-cyan)': undefined }}>
                <div className="trend-label" style={{ marginBottom:6 }}>{t.label}</div>
                <div className="numeric-sg" style={{ fontSize:14, opacity:0.85 }}>Momentum {(t.momentum*100|0)}%</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div style={{ gridArea:'right' }}>
  <TopicDetailPanel topic={selected} onDrill={()=> { setDriversOpen(true); sPing.current?.play(); duckAmbient(); }} />
        {/* Precise mapping of flares and markers for selected topic */}
        {useMemo(()=>{
          (async ()=>{
            if (!selected) return;
            try {
              const [sjson, cjson] = await Promise.all([
                fetchSeries(selected.topic_id),
                fetchChangePoints(selected.topic_id)
              ]);
              // Map change_points dates into 0..1 timeline space
              const dates = (sjson.series||[]).map((p:any)=> new Date(p.date).getTime());
              if (dates.length>1){
                const minT = Math.min(...dates), maxT = Math.max(...dates);
                const cps = (cjson.change_points||[]).map((cp:any)=>{
                  const t = new Date(cp.date).getTime();
                  const frac = (t - minT) / (maxT - minT + 1e-6);
                  return { t: Math.min(1, Math.max(0, frac)), label: cp.type };
                });
                setMarkers(cps);
              }
            } catch {}
          })();
          return null;
        }, [selected])}
        {compareMode && (
          <div className="glass" style={{ marginTop: 12, padding: 10 }}>
            <div className="trend-label" style={{ opacity:0.8, marginBottom:6 }}>Compare</div>
            <div style={{ display:'grid', gap:6 }}>
              {compare.map((c:any)=> (
                <div key={c.topic_id} className="glass" style={{ padding:8, borderRadius:8 }}>
                  <div className="trend-label">{c.label}</div>
                  <div className="numeric-sg" style={{ fontSize:12, opacity:0.8 }}>Momentum {(c.momentum*100|0)}%</div>
                </div>
              ))}
              {compare.length===0 && <div className="trend-label" style={{ opacity:0.7 }}>Choose up to 3 topics to compare</div>}
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div style={{ position:'fixed', left:0, right:0, bottom:0 }}>
        <BottomTimeline playing={playing} onPlayToggle={()=>setPlaying((p: boolean)=>!p)} onScrub={(t: number)=>setTime(t)} changePoints={markers} onMarkerClick={(t:number)=> setTime(t)} onAnnounce={(m:string)=> setAriaMsg(m)} />
      </div>

      <TopicSearch open={searchOpen} onClose={()=> setSearchOpen(false)} topics={topics} onSelect={(t:any)=> { setSelected(t); setAriaMsg(`Selected ${t.label}`); }} />
      <DriversModal open={driversOpen} onClose={()=> setDriversOpen(false)} topicId={selected?.topic_id} />
    </div>
  );
}
