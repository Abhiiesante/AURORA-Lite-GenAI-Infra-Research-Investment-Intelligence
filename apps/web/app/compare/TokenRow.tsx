"use client";
import React, { useRef, useState } from 'react';

type Props = {
  label: string;
  value: number; // 0..1
  onChange: (v: number) => void;
  onGrab?: () => void;
  onSettle?: () => void;
};

export function TokenRow({ label, value, onChange, onGrab, onSettle }: Props){
  const trackRef = useRef(null as unknown as HTMLDivElement | null);
  const [dragging, setDragging] = useState(false);
  const handlePosToValue = (clientX: number) => {
    const el = trackRef.current;
    if (!el) return value;
    const rect = el.getBoundingClientRect();
    const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
    const v = x / rect.width;
    return Math.max(0, Math.min(1, v));
  };
  const onPointerDown = (e: any) => {
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    setDragging(true);
    onGrab?.();
    onChange(handlePosToValue(e.clientX));
  };
  const onPointerMove = (e: any) => {
    if (!dragging) return;
    onChange(handlePosToValue(e.clientX));
  };
  const onPointerUp = (_e: any) => {
    setDragging(false);
    onSettle?.();
  };

  const pct = Math.round(value * 100);

  return (
    <div style={{ display:'grid', gridTemplateColumns:'120px 1fr 56px', alignItems:'center', gap:8, marginBottom:10 }}>
      <div className="trend-label">{label}</div>
      <div
        ref={trackRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onKeyDown={(e)=>{
          const step = e.shiftKey ? 0.1 : 0.02;
          if (e.key === 'ArrowLeft'){ e.preventDefault(); onChange(Math.max(0, value - step)); }
          if (e.key === 'ArrowRight'){ e.preventDefault(); onChange(Math.min(1, value + step)); }
          if (e.key === 'Home'){ e.preventDefault(); onChange(0); }
          if (e.key === 'End'){ e.preventDefault(); onChange(1); }
        }}
        style={{ position:'relative', height:28, borderRadius:20, background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.12)', cursor:'pointer' }}
        aria-label={`${label} weight ${pct}%`}
        role="slider" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}
        tabIndex={0}
      >
        <div style={{ position:'absolute', left:0, top:0, bottom:0, width:`${pct}%`, background:'linear-gradient(90deg, rgba(73,140,255,0.28), rgba(88,74,245,0.24))', borderRadius:20 }} />
        <div style={{ position:'absolute', left:`calc(${pct}% - 10px)`, top:3, width:20, height:20, borderRadius:10, background:'#89a6ff', border:'1px solid #c6d0ff', boxShadow:'0 0 0 3px rgba(137,166,255,0.28)' }} />
      </div>
      <div className="numeric-sg" style={{ textAlign:'right' }}>{pct}%</div>
    </div>
  );
}
