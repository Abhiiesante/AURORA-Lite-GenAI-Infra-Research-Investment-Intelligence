"use client";
import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

export function BottomTimeline({
  onScrub,
  onPlayToggle,
  playing,
  changePoints,
  onMarkerClick,
  onAnnounce
}: {
  onScrub: (t: number)=>void;
  onPlayToggle: ()=>void;
  playing: boolean;
  changePoints: Array<{ t: number; label?: string }>;
  onMarkerClick?: (t: number)=>void;
  onAnnounce?: (msg: string)=>void;
}){
  const trackRef = useRef(null as any);
  const [x, setX] = useState(0);
  const [width, setWidth] = useState(600);

  useEffect(() => {
    if (trackRef.current) setWidth((trackRef.current as HTMLElement).clientWidth);
    const onResize = () => trackRef.current && setWidth((trackRef.current as HTMLElement).clientWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const handleDrag = (_: any, info: any) => {
    const nx = Math.min(Math.max(0, info.point.x - (trackRef.current as HTMLElement).getBoundingClientRect().left), width);
    setX(nx);
    onScrub(nx / width);
    const t = nx/width;
    const hit = changePoints.find(m => Math.abs(m.t - t) < 0.01);
    if (hit && onAnnounce){ onAnnounce(hit.label || 'Change point'); }
  };

  return (
    <div className="glass" style={{ position: 'sticky', bottom: 0, left: 0, right: 0, padding: '12px 16px', backdropFilter: 'blur(10px)', borderTop: '1px solid rgba(255,255,255,0.12)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button aria-label={playing? 'Pause timeline':'Play timeline'} onClick={onPlayToggle} style={{ background: 'var(--aurora-cyan)', border: 'none', color: '#05070A', borderRadius: 6, padding: '8px 12px', cursor: 'pointer' }}>
          {playing? 'Pause':'Play'}
        </button>
        <div ref={trackRef} style={{ position: 'relative', height: 32, flex: 1 }} aria-label="Timeline" role="slider" aria-valuenow={Math.round(x/width*100)} aria-valuemin={0} aria-valuemax={100} tabIndex={0}
          onKeyDown={(e)=>{
            if (e.key==='ArrowLeft'){ const nx = Math.max(0, x-10); setX(nx); onScrub(nx/width); }
            if (e.key==='ArrowRight'){ const nx = Math.min(width, x+10); setX(nx); onScrub(nx/width); }
          }}
        >
          <div style={{ position:'absolute', left:0, right:0, top:14, height:4, background:'rgba(255,255,255,0.12)', borderRadius: 2 }}/>
          {changePoints.map((m, i) => (
            <button key={i} onClick={()=> onMarkerClick?.(m.t)} title={m.label} aria-label={`Change point ${m.label||''}`} style={{ position:'absolute', left:`${m.t*100}%`, top:10, width:8, height:12, background:'transparent', border:'none', cursor:'pointer' }}>
              <div style={{ width:2, height:8, background:'var(--solar-amber)', margin:'2px auto', borderRadius:1 }} />
            </button>
          ))}
          <motion.div drag="x" dragConstraints={trackRef} dragMomentum={false} onDrag={handleDrag} style={{ position:'absolute', top:10, left:x-6, width:12, height:12, borderRadius:'50%', background:'var(--aurora-cyan)', cursor:'grab' }} />
        </div>
      </div>
    </div>
  );
}
