"use client";
import { useEffect, useRef, useState } from "react";

const links = [
  { k: "g m", label: "Market Map", href: "/market-map" },
  { k: "g t", label: "Trends", href: "/trends" },
  { k: "g c", label: "Compare", href: "/compare" },
  { k: "g d", label: "Dashboard", href: "/dashboard" },
  { k: "g j", label: "Jobs", href: "/jobs" },
];

export default function Palette() {
  const [q, setQ] = useState("");
  const inputRef = useRef(null as any);
  useEffect(() => inputRef.current?.focus(), []);
  const items = links.filter(l => l.label.toLowerCase().includes(q.toLowerCase()));
  return (
    <main style={{ padding: 24 }}>
      <h1>Command‑K</h1>
      <input ref={inputRef} value={q} onChange={(e:any)=>setQ(e.target.value)} placeholder="Type to filter…" style={{ width: 360, padding: 8 }} />
      <ul>
        {items.map(i => (
          <li key={i.href}><a href={i.href}>{i.label}</a> <span style={{ opacity: 0.6 }}>({i.k})</span></li>
        ))}
      </ul>
      <p style={{ opacity: 0.7 }}>Tip: Press Ctrl+K / Cmd+K and start typing.</p>
    </main>
  );
}
