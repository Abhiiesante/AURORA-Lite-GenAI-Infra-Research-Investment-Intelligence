"use client";
import { useEffect, useRef, useState } from "react";

export default function FloatingOrb() {
  const [open, setOpen] = useState(false);
  const firstItemRef = useRef(null as HTMLAnchorElement | HTMLButtonElement | null);
  useEffect(()=>{ if (open) firstItemRef.current?.focus(); }, [open]);
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') { setOpen(false); }
    if ((e.key === 'Enter' || e.key === ' ') && (e.target as HTMLElement)?.getAttribute('data-orb') === 'toggle'){
      e.preventDefault(); setOpen((v: boolean)=>!v);
    }
  };
  return (
    <>
      <button
        className="orb glass cyan-glow"
        onClick={()=> setOpen((v: boolean)=>!v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls="orb-menu"
        aria-label="Quick actions"
        data-orb="toggle"
        onKeyDown={onKeyDown}
      >+
      </button>
      {open && (
        <div id="orb-menu" role="menu" aria-label="Quick actions" className="glass" style={{ position:'fixed', right:24, bottom:92, padding:12, borderRadius:12, width:220 }}>
          <a ref={firstItemRef as any} role="menuitem" href="#" onClick={(e)=>{ e.preventDefault(); fetch('/api/seed', { method:'POST' }); alert('Seeding...'); setOpen(false);}}>Seed Sample Data</a>
          <div style={{ height:8 }} />
          <a role="menuitem" href="/market-map">Add Company</a>
        </div>
      )}
    </>
  );
}
