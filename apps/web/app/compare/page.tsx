"use client";
import React, { useMemo, useRef, useState, useEffect } from 'react';
import './compare-tokens.css';
import { CompareCanvas } from './CompareCanvas';
import { computeComposite, computeTorque } from './utils';
import { Howl } from 'howler';
import { clinkSources, thudSources, grabSources, settleSources, shimmerSources, ambientSources } from './audio';
import { TokenRow } from './TokenRow';
import { postCompare, postWeight } from './data';
import { ExplainBox } from './ExplainBox';
import { SnapshotCarousel } from './SnapshotCarousel';
import { captureElementPNG } from './capture';
import { buildCompareSvg } from './svgString';
import { exportCompareBundle } from './exportBundle';

type Company = { id: string; name: string; logo?: string; metrics: Record<string, number> };

export default function ComparatorPage(){
  const [companies, setCompanies] = useState([
    { id: 'company:a', name: 'Alpha', metrics: { revenue_growth: 0.32, arr: 0.4, dev_velocity: 0.7, gross_margin: 0.6 } },
    { id: 'company:b', name: 'Beta', metrics: { revenue_growth: 0.28, arr: 0.5, dev_velocity: 0.62, gross_margin: 0.68 } },
  ] as Company[]);
  const [weights, setWeights] = useState({ revenue_growth: 0.4, arr: 0.2, dev_velocity: 0.25, gross_margin: 0.15 } as Record<string, number>);
  const [ariaMsg, setAriaMsg] = useState('');
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const sClink = useRef(null as unknown as Howl | null);
  const sThud = useRef(null as unknown as Howl | null);
  const sGrab = useRef(null as unknown as Howl | null);
  const sSettle = useRef(null as unknown as Howl | null);
  const sShimmer = useRef(null as unknown as Howl | null);
  const sAmbient = useRef(null as unknown as Howl | null);
  const compareId = useRef(null as unknown as string | null);
  useEffect(()=>{
    try {
      const m = localStorage.getItem('compare_audio_muted');
      const v = localStorage.getItem('compare_audio_volume');
      if (m!=null) setMuted(m==='1');
      if (v!=null) setVolume(Math.max(0, Math.min(1, parseFloat(v))));
    } catch {}
  }, []);
  useEffect(()=>{
    sClink.current = new Howl({ src: clinkSources, volume: (muted?0:0.25)*volume });
    sThud.current = new Howl({ src: thudSources, volume: (muted?0:0.22)*volume });
    sGrab.current = new Howl({ src: grabSources, volume: (muted?0:0.2)*volume });
    sSettle.current = new Howl({ src: settleSources, volume: (muted?0:0.2)*volume });
    sShimmer.current = new Howl({ src: shimmerSources, volume: (muted?0:0.18)*volume });
    sAmbient.current = new Howl({ src: ambientSources, volume: (muted?0:0.12)*volume, loop: true });
    // start ambient softly
    if (!muted){ sAmbient.current.play(); }
    return ()=> { sClink.current?.stop(); sThud.current?.stop(); sGrab.current?.stop(); sSettle.current?.stop(); sShimmer.current?.stop(); sAmbient.current?.stop(); };
  }, [muted, volume]);
  useEffect(()=>{
    try {
      localStorage.setItem('compare_audio_muted', muted? '1':'0');
      localStorage.setItem('compare_audio_volume', String(volume));
    } catch {}
  }, [muted, volume]);

  const left = companies[0];
  const right = companies[1];
  const leftScore = useMemo(()=> left? computeComposite(weights, left.metrics): 0, [left, weights]);
  const rightScore = useMemo(()=> right? computeComposite(weights, right.metrics): 0, [right, weights]);
  const torque = useMemo(()=> computeTorque(leftScore, rightScore), [leftScore, rightScore]);
  const prevTorque = useRef(0);
  const [snapshots, setSnapshots] = useState([] as { id: string; dataUrl: string; title?: string; timestamp: string }[]);
  const [ducking, setDucking] = useState(0);
  useEffect(()=>{
    const delta = Math.abs(torque - prevTorque.current);
    if (delta > 0.03){
      sThud.current?.play();
      setDucking(0.6);
      // simple ambient duck
      const amb = sAmbient.current;
      if (amb){
        const base = (muted?0:0.12)*volume;
        amb.fade(base, base*0.4, 80);
        setTimeout(()=> amb.fade(base*0.4, base, 180), 200);
      }
      setTimeout(()=> setDucking(0), 300);
    }
    prevTorque.current = torque;
  }, [torque]);

  // Create a compare session on mount (dev route)
  useEffect(()=>{
    (async ()=>{
      try{
  const ids = companies.map((c: Company)=> c.id);
        const { compare_id } = await postCompare({ companies: ids, weights });
        compareId.current = compare_id;
      }catch{
        // ignore; can work offline/local too
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="compare-bg" style={{ display:'grid', gridTemplateRows:'64px auto 120px', gridTemplateColumns:'220px 1fr 360px', gridTemplateAreas:`
      'top top top'
      'left main right'
      'bottom bottom bottom'
    `, gap:12, padding:12 }}>
      <div style={{ gridArea:'top', display:'flex', alignItems:'center', gap:12 }}>
        <div className="glass" style={{ padding:'8px 12px' }}>
          <span className="title-orbitron" style={{ fontSize:22 }}>Comparator — Weigh the Options</span>
        </div>
        <div style={{ display:'flex', gap:8, alignItems:'center' }}>
          <button className="glass" style={{ padding:'8px 12px' }} onClick={()=>{
            // Simple auto-benchmark: equalize weights
            const keys = Object.keys(weights);
            const eq = 1 / Math.max(1, keys.length);
            const next: Record<string, number> = {};
            for (const k of keys) next[k] = eq;
            setWeights(next);
            setAriaMsg('Auto-benchmark applied');
            sShimmer.current?.play();
          }}>Auto-benchmark</button>
          <button className="glass" style={{ padding:'8px 12px' }} onClick={async()=>{
            // Save snapshot thumbnail from main area
            const main = document.querySelector('[style*="grid-area:\'main\'"]') as HTMLElement | null;
            const host = main?.querySelector('.glass') as HTMLElement | null;
            if (host){
              const dataUrl = await captureElementPNG(host);
              setSnapshots((s: { id: string; dataUrl: string; title?: string; timestamp: string }[])=> [{ id: Math.random().toString(36).slice(2,10), dataUrl, timestamp: new Date().toISOString() }, ...s].slice(0,12));
              sShimmer.current?.play();
            }
          }}>Save</button>
          <button className="glass" style={{ padding:'8px 12px' }} onClick={async()=>{
            const main = document.querySelector('[style*="grid-area:\'main\'"]') as HTMLElement | null;
            const host = main?.querySelector('.glass') as HTMLElement | null;
            if (!host) return;
            const rect = host.getBoundingClientRect();
            const width = Math.round(rect.width);
            const height = Math.round(rect.height);
            const svgStr = buildCompareSvg({
              width, height,
              title: 'Comparator — Weigh the Options',
              asOf: new Date().toLocaleString(),
              leftName: left?.name,
              rightName: right?.name,
              leftScore,
              rightScore,
              weights,
            });
            const dataUrl = await captureElementPNG(host);
            const a = document.createElement('a');
            a.href = dataUrl; a.download = `compare_${Date.now()}.png`; a.click();
            sShimmer.current?.play();
          }}>PNG</button>
          <button className="glass" style={{ padding:'8px 12px' }} onClick={async()=>{
            const main = document.querySelector('[style*="grid-area:\'main\'"]') as HTMLElement | null;
            const host = main?.querySelector('.glass') as HTMLElement | null;
            if (!host) return;
            const rect = host.getBoundingClientRect();
            const width = Math.round(rect.width);
            const height = Math.round(rect.height);
            const svgStr = buildCompareSvg({ width, height, title:'Comparator — Weigh the Options', asOf: new Date().toLocaleString(), leftName: left?.name, rightName: right?.name, leftScore, rightScore, weights });
            const blob = new Blob([svgStr], { type:'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = `compare_overlay_${Date.now()}.svg`; a.click(); URL.revokeObjectURL(url);
            sShimmer.current?.play();
          }}>SVG</button>
          <button className="glass" style={{ padding:'8px 12px' }} onClick={async()=>{
            const main = document.querySelector('[style*="grid-area:\'main\'"]') as HTMLElement | null;
            const host = main?.querySelector('.glass') as HTMLElement | null;
            if (!host) return;
            const rect = host.getBoundingClientRect();
            const width = Math.round(rect.width);
            const height = Math.round(rect.height);
            const svgStr = buildCompareSvg({ width, height, title:'Comparator — Weigh the Options', asOf: new Date().toLocaleString(), leftName: left?.name, rightName: right?.name, leftScore, rightScore, weights });
            const meta = { left: left?.id, right: right?.id, leftScore, rightScore, weights, timestamp: new Date().toISOString() };
            await exportCompareBundle({ host, svgStr, width, height, meta });
            sShimmer.current?.play();
          }}>PDF</button>
          <div style={{ width:1, height:24, background:'rgba(255,255,255,0.18)' }} />
          <button className="trend-label" onClick={()=> setMuted((m: boolean)=>!m)} style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.16)', color:'var(--starlight)', borderRadius:6, padding:'6px 8px' }}>{muted? '🔇':'🔊'}</button>
          <input aria-label="Volume" type="range" min={0} max={1} step={0.05} value={volume} onChange={(e)=> setVolume(parseFloat(e.target.value))} style={{ width:120 }} />
        </div>
      </div>

      <div style={{ gridArea:'left' }}>
        <div className="glass" style={{ padding:10, height:'100%' }}>
          <div className="trend-label" style={{ marginBottom:8 }}>Company Library</div>
          <div style={{ display:'grid', gap:8 }}>
            {companies.map((c: Company)=> (
              <div key={c.id} className="glass" style={{ padding:8, borderRadius:8 }}>{c.name}</div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ gridArea:'main', position:'relative' }}>
        <div className="glass" style={{ position:'absolute', inset:0, overflow:'hidden', filter: ducking? `brightness(${1-ducking*0.15})` : undefined }}>
          <CompareCanvas torque={torque} slabs={[
            { id: left?.id||'left', name: left?.name||'', color:'#24324a' },
            { id: right?.id||'right', name: right?.name||'', color:'#223149' }
          ]} />
        </div>
      </div>

      <div style={{ gridArea:'right' }}>
        <div className="glass" style={{ padding:12, marginBottom:12 }}>
          <div className="trend-label" style={{ marginBottom:8 }}>Weights</div>
          {Object.keys(weights).map((k)=> (
            <TokenRow
              key={k}
              label={k}
              value={weights[k]}
              onGrab={()=> sGrab.current?.play()}
              onSettle={() => sSettle.current?.play()}
              onChange={async (v)=>{
                setWeights((w: Record<string, number>)=> ({ ...w, [k]: v }));
                setAriaMsg(`Weight ${k} set to ${(v*100|0)}%`);
                sClink.current?.play();
                const id = compareId.current;
                if (id){
                  try{
                    await postWeight(id, { metric: k, delta: v - (weights[k]||0) });
                  }catch{}
                }
              }}
            />
          ))}
          <div className="glass" style={{ padding:8, marginTop:8, display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
            <div>
              <div className="trend-label" style={{ marginBottom:4 }}>{left?.name||'—'}</div>
              <div className="numeric-sg" style={{ fontSize:20 }}>{(leftScore*100|0)}%</div>
            </div>
            <div>
              <div className="trend-label" style={{ marginBottom:4 }}>{right?.name||'—'}</div>
              <div className="numeric-sg" style={{ fontSize:20 }}>{(rightScore*100|0)}%</div>
            </div>
          </div>
        </div>
        <ExplainBox leftName={left?.name} rightName={right?.name} leftScore={leftScore} rightScore={rightScore} />
      </div>

      <div style={{ gridArea:'bottom' }}>
        <SnapshotCarousel items={snapshots} />
      </div>

      <div aria-live="polite" className="trend-label" style={{ position:'absolute', left:-99999, top:'auto', width:1, height:1, overflow:'hidden' }}>{ariaMsg}</div>
    </div>
  );
}
 
