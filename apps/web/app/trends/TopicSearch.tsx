"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";
import Fuse from "fuse.js";

type Topic = { topic_id: string; label: string; momentum: number; trend_state: 'rising'|'stable'|'declining' };

export function TopicSearch({ open, onClose, topics, onSelect }: {
  open: boolean;
  onClose: ()=>void;
  topics: Topic[];
  onSelect: (topic: Topic)=>void;
}){
  const [q, setQ] = useState("");
  const inputRef = useRef(null as unknown as HTMLInputElement | null);
  const listRef = useRef(null as unknown as HTMLDivElement | null);

  const fuse = useMemo(()=> new Fuse(topics, { keys: ["label"], threshold: 0.35 }), [topics]);
  type FuseResult<T> = { item: T };
  const results = useMemo(()=> q.trim()? (fuse.search(q) as unknown as FuseResult<Topic>[]).slice(0, 20).map((r)=>r.item) : topics.slice(0, 20), [q, fuse, topics]);

  useEffect(()=>{
    if (open){ setTimeout(()=> inputRef.current?.focus(), 10); }
  }, [open]);

  useEffect(()=>{
    const onKey = (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === 'Escape'){ e.preventDefault(); onClose(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="search-title" className="glass" style={{ position:'fixed', inset:0, background:'rgba(5,7,10,0.6)', display:'grid', placeItems:'start center', paddingTop: 80, zIndex: 60 }}>
      <div style={{ width: 720, maxWidth: '95vw' }}>
        <div className="glass" style={{ padding: 12, borderRadius: 10, border:'1px solid rgba(255,255,255,0.18)', backdropFilter:'blur(10px)' }}>
          <div id="search-title" className="trend-label" style={{ opacity: 0.8, marginBottom: 6 }}>Search topics</div>
          <input ref={inputRef} value={q} onChange={e=>setQ(e.target.value)} placeholder="Type to search…" aria-label="Search topics" style={{ width:'100%', background:'transparent', border:'none', outline:'none', color:'var(--starlight)', padding:'8px 6px' }} />
        </div>
        <div ref={listRef} className="glass" style={{ marginTop: 10, maxHeight: '50vh', overflow:'auto', borderRadius: 10, border:'1px solid rgba(255,255,255,0.18)' }}>
          {results.map((t: Topic)=> (
            <button key={t.topic_id} onClick={()=>{ onSelect(t); onClose(); }} className="trend-label" style={{ display:'flex', justifyContent:'space-between', width:'100%', textAlign:'left', padding:'10px 12px', background:'transparent', border:'none', color:'var(--starlight)', cursor:'pointer' }}>
              <span>{t.label}</span>
              <span className="numeric-sg" style={{ opacity: 0.8 }}>Momentum {(t.momentum*100|0)}%</span>
            </button>
          ))}
          {results.length===0 && (
            <div className="trend-label" style={{ padding: 12, opacity: 0.7 }}>No matches</div>
          )}
        </div>
        <div className="trend-label" style={{ marginTop: 8, opacity: 0.7 }}>Esc to close • Enter to select</div>
      </div>
    </div>
  );
}
