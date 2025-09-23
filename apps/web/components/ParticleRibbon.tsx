"use client";
import React, { useEffect, useRef } from "react";

type Props = { opacity?: number };

export default function ParticleRibbon({ opacity = 0.18 }: Props) {
  const ref = useRef(null as HTMLCanvasElement | null);
  const raf = useRef(null as number | null);
  const prefersReduced = typeof window !== 'undefined' && (
    (document?.documentElement?.classList?.contains('reduce-motion')) ||
    (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  );

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    let running = true;
    const DPR = Math.min(2, window.devicePixelRatio || 1);
    let w = canvas.clientWidth, h = canvas.clientHeight;
    const resize = () => {
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = Math.floor(w * DPR); canvas.height = Math.floor(h * DPR);
      ctx.scale(DPR, DPR);
    };
    const onResize = () => { ctx.setTransform(1,0,0,1,0,0); resize(); };
    resize();
    window.addEventListener('resize', onResize);

    const N = 220;
    const pts: { x:number; y:number; vx:number; vy:number; r:number }[] = new Array(N).fill(0).map(()=>({
      x: Math.random()*w,
      y: Math.random()*h,
      vx: (Math.random()-0.5)*0.08,
      vy: (Math.random()-0.5)*0.08,
      r: 0.8 + Math.random()*1.2,
    }));

    const loop = () => {
      if (!running) return;
      ctx.clearRect(0,0,w,h);
      ctx.globalCompositeOperation = 'lighter';
      for (const p of pts){
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x += w; if (p.x > w) p.x -= w;
        if (p.y < 0) p.y += h; if (p.y > h) p.y -= h;
        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, 12);
        grad.addColorStop(0, 'rgba(0,240,255,0.55)');
        grad.addColorStop(1, 'rgba(178,102,255,0.0)');
        ctx.fillStyle = grad;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2); ctx.fill();
      }
      raf.current = requestAnimationFrame(loop);
    };

    if (!prefersReduced) raf.current = requestAnimationFrame(loop);
    return () => { running = false; if (raf.current) cancelAnimationFrame(raf.current); window.removeEventListener('resize', onResize); };
  }, [prefersReduced]);

  return <canvas ref={ref} style={{ position:'absolute', inset:0, opacity, pointerEvents:'none' }} aria-hidden="true" />;
}
