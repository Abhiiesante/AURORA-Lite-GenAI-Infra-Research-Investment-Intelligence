"use client";
import { useEffect, useMemo, useRef } from "react";

function Spark({ color = "#00f0ff" }: { color?: string }){
  const ref = useRef(null as HTMLCanvasElement | null);
  const data = useMemo(()=> Array.from({length:36}, (_,i)=> 0.6 + Math.sin(i/3)*0.2 + (Math.random()-0.5)*0.1), []);
  useEffect(()=>{
    const c = ref.current; if(!c) return; const dpr = window.devicePixelRatio||1; const w = c.clientWidth; const h = c.clientHeight; c.width = Math.round(w*dpr); c.height = Math.round(h*dpr);
    const ctx = c.getContext('2d'); if(!ctx) return; ctx.scale(dpr,dpr); ctx.clearRect(0,0,w,h);
    ctx.globalAlpha = 0.9; ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath();
    for(let i=0;i<data.length;i++){
      const x = (i/(data.length-1))*w; const y = h - data[i]*h;
      if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    ctx.stroke();
    ctx.globalAlpha = 0.16; ctx.fillStyle = color; ctx.lineTo(w,h); ctx.lineTo(0,h); ctx.closePath(); ctx.fill();
  },[data,color]);
  return <canvas ref={ref} style={{width:'100%', height:34, display:'block'}} aria-hidden />
}

export function KPITile({ label, value, color = "cyan" }: { label: string; value: string; color?: "cyan"|"violet"|"orange" }) {
  const ref = useRef(null as any);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    let id = requestAnimationFrame(function pulse(t){
      const k = (Math.sin(t/700)+1)/2; // 0..1
      el.style.boxShadow = color === 'cyan' ? `0 0 ${6+12*k}px rgba(0,240,255,${0.25+0.35*k})` : color==='violet' ? `0 0 ${6+12*k}px rgba(178,102,255,${0.22+0.32*k})` : `0 0 ${6+12*k}px rgba(255,122,0,${0.22+0.32*k})`;
      id = requestAnimationFrame(pulse);
    });
    return ()=> cancelAnimationFrame(id);
  }, [color]);
  const sparkColor = color==='cyan'? '#00f0ff' : color==='violet'? '#b266ff' : '#ff7a00';
  return (
    <div ref={ref} className="kpi glass">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      <Spark color={sparkColor} />
    </div>
  );
}

export function KPIRow() {
  return (
    <div className="kpis">
      <KPITile label="Infra Spend" value="$12,340" color="cyan" />
      <KPITile label="Active Models" value="18" color="violet" />
      <KPITile label="Anomaly Alerts" value="3" color="orange" />
      <KPITile label="Signal Coverage" value="92%" color="cyan" />
    </div>
  );
}
