"use client";
import React, { useEffect, useRef, useState } from "react";
import { useCmdKStore } from "@/app/cmdkStore";
import { sfx } from "@/app/sfx";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { useCommandK, CmdKResult } from "@/app/commandk/useCommandK";
import ThumbnailCarousel from "@/components/ThumbnailCarousel";
import ParticleRibbon from "@/components/ParticleRibbon";

const MiniConstellation = dynamic(() => import("@/components/MiniConstellation"), { ssr: false, loading: () => <div className="skeleton" style={{ height: 160 }} /> });

export default function CommandKOverlay() {
  const { isOpen, close, query, setQuery } = useCmdKStore();
  const { suggest, execute, getThumbnail } = useCommandK();
  const inputRef = useRef(null as HTMLInputElement | null);
  const previewRef = useRef(null as HTMLDivElement | null);
  const [active, setActive] = useState(0);
  const [results, setResults] = useState([] as CmdKResult[]);
  const [thumbUrl, setThumbUrl] = useState(null as string | null);
  const [executing, setExecuting] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (isOpen) { inputRef.current?.focus(); sfx.open(); } else { sfx.close(); }
  }, [isOpen]);

  // Debounced search
  useEffect(() => {
    if (!isOpen) return;
    const q = query.trim();
    const id = setTimeout(async () => {
      try {
        const data = await suggest(q, 12, "global");
        setResults(data.results || []);
        setActive(0);
      } catch (e) { /* ignore */ }
    }, 120);
    return () => clearTimeout(id);
  }, [query, isOpen, suggest]);

  // Load preview thumbnail for active
  useEffect(() => {
    const item = results[active];
    if (!item) { setThumbUrl(null); return; }
    if (item.thumbnail_url) { setThumbUrl(item.thumbnail_url); return; }
    if (item.id) {
      getThumbnail(item.id, "160x100").then((r: { url: string }) => setThumbUrl(r.url)).catch(() => setThumbUrl(null));
    }
  }, [active, results, getThumbnail]);

  const prefersReduced = typeof window !== 'undefined' && (
    (document?.documentElement?.classList?.contains('reduce-motion')) ||
    (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  );

  useEffect(() => {
    if (!isOpen) return; // only attach when open
    if (prefersReduced) return;
    const el = previewRef.current; if (!el) return;
    const onMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      const cx = rect.left + rect.width/2; const cy = rect.top + rect.height/2;
      const dx = (e.clientX - cx) / rect.width; const dy = (e.clientY - cy) / rect.height;
      el.style.transform = `perspective(800px) rotateX(${(-dy*4).toFixed(2)}deg) rotateY(${(dx*4).toFixed(2)}deg)`;
    };
    const onLeave = () => { el.style.transform = 'none'; };
    window.addEventListener('mousemove', onMove);
    el.addEventListener('mouseleave', onLeave);
    return () => { window.removeEventListener('mousemove', onMove); el?.removeEventListener('mouseleave', onLeave); };
  }, [prefersReduced, isOpen]);

  if (!isOpen) return null;

  const activeItem = results[active];

  const handleEnter = async (e: any) => {
    const pick = results[active]; if (!pick) return;
    if (e.altKey) {
      // Open action menu alternative: trigger memo if available
      const a = pick.actions?.find((x: { id: string }) => x.id !== 'open') || pick.actions?.[0];
      if (a) {
        sfx.confirm();
        setExecuting(true);
        setProgress(0);
        try {
          await execute(a.id, { entity: pick.id }, {
            onProgress: (evt: any) => {
              if (evt?.type === 'progress' && typeof evt?.data?.progress === 'number') {
                setProgress(Math.min(100, Math.max(0, evt.data.progress)));
              }
              if (evt?.type === 'done') {
                setProgress(100);
              }
            }
          });
        } finally {
          setExecuting(false);
          setTimeout(() => { setProgress(0); }, 400);
          close();
        }
      }
      return;
    }
    if (e.shiftKey) {
      // Split view: navigate with query param
      sfx.confirm(); window.location.href = `/dossier?split=1&entity=${encodeURIComponent(pick.id)}`; return;
    }
    // Default open
    sfx.confirm();
    if (pick.type === 'company') window.location.href = `/companies/${encodeURIComponent(pick.id.split(':')[1] || pick.id)}`;
    else if (pick.type === 'topic') window.location.href = `/trends?topic=${encodeURIComponent(pick.id)}`;
    else window.location.href = `/search?q=${encodeURIComponent(pick.title)}`;
  };

  const overlayVariants = {
    hidden: { opacity: 0, y: -18, scale: 0.996 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.30, ease: [0.16,0.84,0.24,1] as any } },
    exit: { opacity: 0, y: -12, transition: { duration: 0.18 } },
  };

  return (
    <div className="cmdk-overlay" onClick={close} role="dialog" aria-modal="true" aria-label="Command palette">
  <motion.div initial="hidden" animate="visible" exit="exit" variants={overlayVariants} className="cmdk-panel glass" onClick={(e: any) => e.stopPropagation()} style={{ position:'relative', overflow:'hidden' }}>
        <ParticleRibbon opacity={0.16} />
        <div style={{ gridColumn: '1 / -1', display:'flex', alignItems:'center', gap:8 }}>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search everything — companies, topics, memos, commands (try: ‘>generate memo pinecone’ )"
            className="cmdk-input"
            aria-autocomplete="list"
            aria-controls="cmdk-listbox"
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") { e.preventDefault(); setActive((a: number) => { sfx.move(); return Math.min(a + 1, Math.max(0, results.length - 1)); }); }
              else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a: number) => { sfx.move(); return Math.max(a - 1, 0); }); }
              else if (e.key === "Enter") { handleEnter(e); }
              else if (e.key === "Escape") { close(); }
            }}
          />
          {executing && (
            <div style={{ display:'flex', alignItems:'center', gap:8 }}>
              <div className="spinner" aria-label="Executing" />
              <div aria-label="Progress" style={{ width:96, height:6, borderRadius:999, background:'rgba(255,255,255,0.12)', overflow:'hidden' }}>
                <div style={{ width: `${progress}%`, height:'100%', background:'linear-gradient(90deg, var(--cyan), var(--violet))' }} />
              </div>
            </div>
          )}
        </div>
        {/* Help/Shortcuts panel if query starts with 'help' */}
        {String(query).trim().toLowerCase().startsWith('help') ? (
          <div className="cmdk-list" role="region" aria-label="Shortcuts help" style={{ lineHeight:1.6 }}>
            <div className="glass" style={{ padding:12, borderRadius:12 }}>
              <strong style={{ display:'block', marginBottom:6 }}>Shortcuts</strong>
              <ul style={{ margin:0, paddingLeft:18 }}>
                <li><kbd>⌘K</kbd>/<kbd>Ctrl</kbd>+<kbd>K</kbd>: Toggle command palette</li>
                <li><kbd>/</kbd>: Open command palette and focus search</li>
                <li><kbd>↑</kbd>/<kbd>↓</kbd>: Navigate results</li>
                <li><kbd>Enter</kbd>: Open selection</li>
                <li><kbd>Shift</kbd>+<kbd>Enter</kbd>: Open in split view</li>
                <li><kbd>Alt</kbd>+<kbd>Enter</kbd>: Run secondary action (e.g., Generate Memo)</li>
                <li><kbd>Esc</kbd>: Close palette</li>
              </ul>
              <button onClick={() => setQuery("")} className="cmdk-item" style={{ marginTop:10 }}>Back to search</button>
            </div>
          </div>
        ) : (
          <div id="cmdk-listbox" role="listbox" className="cmdk-list">
          {results.map((i: CmdKResult, idx: number) => (
            <motion.button
              key={i.id}
              role="option"
              aria-selected={idx === active}
              className="cmdk-item"
              style={{ outline: idx===active? '2px solid rgba(0,240,255,0.5)': undefined }}
              onMouseEnter={()=> setActive(idx)}
              onClick={()=> { sfx.confirm(); setActive(idx); void handleEnter({ key: 'Enter', altKey:false, shiftKey:false, preventDefault(){}, stopPropagation(){}} as any); }}
              whileHover={{ scale: 1.02 }} transition={{ duration: 0.14, ease: [0.2,0.9,0.3,1] as any }}
            >
              <span className="cmdk-label">{i.title}</span>
              <span className="cmdk-k">{i.type}</span>
            </motion.button>
          ))}
          </div>
        )}
  <aside className="cmdk-preview" aria-label="Preview" ref={previewRef}>
          {prefersReduced ? (
            <div className="preview-box">{activeItem ? activeItem.title : '—'}</div>
          ) : thumbUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={thumbUrl} alt="Preview thumbnail" style={{ width:'100%', height:220, objectFit:'cover', borderRadius:10 }} />
          ) : (
            <div style={{ width: '100%', height: 220 }}>
              <MiniConstellation />
            </div>
          )}
        </aside>
        <div className="cmdk-hint" style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <span>⌘K / Ctrl+K • / search • Enter = open • Shift+Enter = splitview • Esc = close</span>
          <label style={{ display:'inline-flex', gap:6, alignItems:'center', fontSize:12 }}>
            <input type="checkbox" onChange={(e:any)=>{
              const on = e.target.checked; try { localStorage.setItem('aurora_reduce_motion', on? '1':'0'); } catch {}
              document.documentElement.classList.toggle('reduce-motion', on);
            }} defaultChecked={typeof window!=='undefined' && localStorage.getItem('aurora_reduce_motion')==='1'} />
            Prefers reduced motion
          </label>
        </div>
        <div className="sr-only" aria-live="polite" aria-atomic="true">{activeItem ? `Selected ${activeItem.title}` : ''}</div>
        <div style={{ gridColumn: '1 / -1' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 }}>
            <button onClick={() => setQuery('help: shortcuts')} style={{ fontSize:12, opacity:0.8, textDecoration:'underline' }}>Shortcuts</button>
          </div>
          <ThumbnailCarousel items={(results || []).slice(0, 10).map((r: CmdKResult) => ({ id: r.id, label: r.title }))} />
        </div>
      </motion.div>
    </div>
  );
}
