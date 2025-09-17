"use client";
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useCmdKStore } from "@/app/cmdkStore";
import { useSfxStore } from "@/app/sfxStore";

const tabs = [
  { href: "/market-map", label: "Market Map" },
  { href: "/trends", label: "Trends" },
  { href: "/compare", label: "Compare" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/kg", label: "KG Explorer" },
  { href: "/palette", label: "Command‑K" },
  { href: "/jobs", label: "Jobs" },
  { href: "/gate-status", label: "Gate Status" },
];

export default function NavBar() {
  const path = usePathname();
  const toggle = useCmdKStore((s) => s.toggle);
  const sfxEnabled = useSfxStore((s) => s.enabled);
  const toggleSfx = useSfxStore((s) => s.toggle);
  const [signal, setSignal] = useState(72);
  const ringRef = useRef(null as HTMLDivElement | null);
  const animRef = useRef(null as any);
  const degRef = useRef(0);
  // Fetch a dashboard snapshot (company 1 by default) and extract signal_score
  useEffect(() => {
    let mounted = true;
    const fetchSignal = async () => {
      try {
        const res = await fetch(`/api/dashboard?id=1&window=90d`, { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        const raw = Number((data?.kpis?.signal_score ?? data?.kpis?.sentiment_30d ?? 55));
        if (!isFinite(raw)) return;
        const pct = Math.max(0, Math.min(100, raw));
        if (mounted) setSignal(pct);
      } catch { /* ignore */ }
    };
    fetchSignal();
    const t = setInterval(fetchSignal, 60000);
    return () => { mounted = false; clearInterval(t); };
  }, []);
  // Animate ring arc via CSS custom property
  useEffect(() => {
    const el = ringRef.current;
    if (!el) return;
    const start = degRef.current;
    const end = (signal/100) * 360;
    const dur = 520; // ms
    const t0 = performance.now();
    if (animRef.current) cancelAnimationFrame(animRef.current);
    const ease = (k: number) => 0.5 - 0.5 * Math.cos(Math.PI * k);
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / dur);
      const val = start + (end - start) * ease(k);
      el.style.setProperty('--ring', `${Math.round(val)}deg`);
      if (k < 1) {
        animRef.current = requestAnimationFrame(step);
      } else {
        degRef.current = end;
        animRef.current = null;
      }
    };
    animRef.current = requestAnimationFrame(step);
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, [signal]);
  return (
    <nav className="navbar glass">
      <div className="brand" aria-hidden="true">
        <div className="avatar" />
        <div ref={ringRef} className="ring-badge" title="Signal Health" aria-label={`Signal health ${Math.round(signal)} percent`}>
          <span className="ring-text">{Math.round(signal)}%</span>
        </div>
      </div>
      <div className="tabs">
        {tabs.map((t) => {
          const active = path?.startsWith(t.href) ?? false;
          return (
            <Link key={t.href} href={t.href} className={active ? "active" : ""} aria-current={active? 'page': undefined} aria-label={`Go to ${t.label}`}>
              {t.label}
            </Link>
          );
        })}
      </div>
      <div style={{ marginLeft: "auto" }} />
      <button className="glass" aria-pressed={sfxEnabled} aria-label={sfxEnabled? 'Disable sounds':'Enable sounds'} onClick={toggleSfx} style={{ marginRight: 8 }}>
        {sfxEnabled ? '🔊' : '🔈'}
      </button>
      <input className="cmdk cyan-glow" placeholder="Search · ⌘K" onFocus={(e)=> e.currentTarget.classList.add('cyan-glow')} onBlur={(e)=> e.currentTarget.classList.remove('cyan-glow')} onKeyDown={(e:any)=>{ if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){ e.preventDefault(); toggle(); } }} onClick={toggle} />
    </nav>
  );
}
