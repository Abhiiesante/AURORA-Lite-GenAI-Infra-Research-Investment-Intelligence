"use client";
import React, { useEffect, useRef, useState } from "react";
import { useCommandK } from "@/app/commandk/useCommandK";

type Item = { id: string; label: string };
type Props = { items: Item[] };

export default function ThumbnailCarousel({ items }: Props) {
  const { getThumbnail } = useCommandK();
  const [urls, setUrls] = useState({} as Record<string, string>);
  const [focusIdx, setFocusIdx] = useState(0);
  const rowRef = useRef(null as HTMLDivElement | null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      for (const it of items.slice(0, 12)) {
        try {
          const { url } = await getThumbnail(it.id, '160x100');
          if (!cancelled) setUrls((u: Record<string, string>) => ({ ...u, [it.id]: url }));
        } catch {}
      }
    })();
    return () => { cancelled = true; };
  }, [items, getThumbnail]);

  useEffect(() => {
    const el = rowRef.current?.children[focusIdx] as HTMLElement | undefined;
    el?.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }, [focusIdx]);

  return (
    <div aria-label="Thumbnails" role="group" className="glass" style={{ padding: 8 }}>
      <div
        ref={rowRef}
        className="thumb-row"
        style={{ display: 'flex', gap: 8, overflowX: 'auto' }}
        tabIndex={0}
  onKeyDown={(e) => {
          if (e.key === 'ArrowRight') setFocusIdx((i: number) => Math.min(i + 1, items.length - 1));
          if (e.key === 'ArrowLeft') setFocusIdx((i: number) => Math.max(i - 1, 0));
        }}
      >
        {items.map((it, idx) => (
          <div
            key={it.id}
            role="button"
            tabIndex={0}
            aria-label={`Thumbnail ${it.label}`}
            className="thumb"
            style={{ width: 160, height: 100, borderRadius: 10, border: '1px solid rgba(255,255,255,0.12)', outline: idx===focusIdx? '2px solid rgba(0,240,255,0.4)': undefined, background: 'rgba(255,255,255,0.04)' }}
            onFocus={() => setFocusIdx(idx)}
          >
            {urls[it.id] ? <img src={urls[it.id]} alt="" width={160} height={100} style={{ display:'block', borderRadius:10 }} /> : <div className="skeleton" style={{ height: '100%' }} />}
          </div>
        ))}
      </div>
    </div>
  );
}
