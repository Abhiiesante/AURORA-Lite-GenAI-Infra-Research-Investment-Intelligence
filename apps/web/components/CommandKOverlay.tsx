"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useCmdKStore } from "@/app/cmdkStore";
import Fuse from "fuse.js";
import { sfx } from "@/app/sfx";
import dynamic from "next/dynamic";

const MiniConstellation = dynamic(() => import("@/components/MiniConstellation"), { ssr: false, loading: () => <div className="skeleton" style={{ height: 160 }} /> });

const links = [
  { k: "g m", label: "Market Map", href: "/market-map", icon: "🗺️" },
  { k: "g t", label: "Trends", href: "/trends", icon: "📈" },
  { k: "g c", label: "Compare", href: "/compare", icon: "⚖️" },
  { k: "g d", label: "Dashboard", href: "/dashboard", icon: "📊" },
  { k: "g k", label: "KG Explorer", href: "/kg", icon: "🧠" },
  { k: "g j", label: "Jobs", href: "/jobs", icon: "💼" },
  { k: "g s", label: "Gate Status", href: "/gate-status", icon: "🚦" },
];

type LinkItem = { k: string; label: string; href: string; icon?: string };

export default function CommandKOverlay() {
  const { isOpen, close, query, setQuery } = useCmdKStore();
  const inputRef = useRef(null as HTMLInputElement | null);
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (isOpen) { inputRef.current?.focus(); sfx.open(); } else { sfx.close(); }
  }, [isOpen]);

  const items: LinkItem[] = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return links;
    const fuse = new Fuse(links, { includeScore: true, threshold: 0.42, keys: ["label", "k"] });
    return fuse.search(q).map((r) => r.item);
  }, [query]);

  if (!isOpen) return null;

  const activeItem = items[active];
  const prefersReduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  return (
    <div className="cmdk-overlay" onClick={close} role="dialog" aria-modal="true" aria-label="Command palette">
      <div className="cmdk-panel glass" onClick={(e) => e.stopPropagation()}>
        <div style={{ gridColumn: '1 / -1' }}>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search · destinations · actions"
            className="cmdk-input"
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault(); setActive((a: number) => { sfx.move(); return Math.min(a + 1, items.length - 1); });
              } else if (e.key === "ArrowUp") {
                e.preventDefault(); setActive((a: number) => { sfx.move(); return Math.max(a - 1, 0); });
              } else if (e.key === "Enter") {
                const pick = items[active]; if (pick) { sfx.confirm(); window.location.href = pick.href; }
              } else if (e.key === "Escape") {
                close();
              }
            }}
          />
        </div>
        <div className="cmdk-list">
          {items.map((i: LinkItem, idx: number) => (
            <a key={i.href} href={i.href} className="cmdk-item" style={{ outline: idx===active? '2px solid rgba(0,240,255,0.5)': undefined }} onMouseEnter={()=> setActive(idx)}>
              <span aria-hidden="true" style={{ marginRight: 8 }}>{i.icon ?? ' '}</span>
              <span className="cmdk-label">{i.label}</span>
              <span className="cmdk-k">{i.k}</span>
            </a>
          ))}
        </div>
        <aside className="cmdk-preview" aria-label="Preview">
          {prefersReduced ? (
            <div className="preview-box">{activeItem ? activeItem.label : '—'}</div>
          ) : (
            <div style={{ width: '100%', height: 220 }}>
              <MiniConstellation />
            </div>
          )}
        </aside>
        <div className="cmdk-hint">Press Esc to close · Enter to navigate</div>
        {/* A11y live region to announce the active selection */}
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          {activeItem ? `Selected ${activeItem.label}` : ''}
        </div>
      </div>
    </div>
  );
}
