"use client";
import { memo, useEffect } from "react";

type Company = { id: number; canonical_name: string; segments?: string[] | string; status?: string };

function CompanyGridImpl({ companies }: { companies: Company[] }) {
  useEffect(() => {
    const cards = document.querySelectorAll('.card3d') as NodeListOf<HTMLElement>;
    const onMove = (e: MouseEvent) => {
      cards.forEach((c) => {
        const rect = c.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width; // 0..1
        const y = (e.clientY - rect.top) / rect.height; // 0..1
        const rx = (0.5 - y) * 6; // deg
        const ry = (x - 0.5) * 6;
        const inner = c.querySelector('.inner') as HTMLElement | null;
        if (inner) inner.style.setProperty('--rx', rx.toFixed(2) + 'deg');
        if (inner) inner.style.setProperty('--ry', ry.toFixed(2) + 'deg');
      })
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);
  return (
    <div className="grid" role="list" aria-label="Companies">
      {companies.map((co) => (
        <div key={co.id} className="card3d" role="listitem">
          <a href={`/companies/${co.id}`} className="inner glass" style={{ display:'block', padding:14 }} aria-label={`Open ${co.canonical_name} details`}>
            <div style={{ fontWeight:700 }}>
              <span aria-hidden>{co.canonical_name}</span>
            </div>
            <div style={{ opacity:0.7, fontSize:12 }}>{Array.isArray(co.segments) ? co.segments.join(', ') : (co.segments||'')}</div>
            <div style={{ marginTop:8 }}>
              <span className="glass" style={{ padding:'2px 8px', borderRadius:8, fontSize:12, color:'#00f0ff' }}>{co.status||'Monitoring'}</span>
            </div>
          </a>
        </div>
      ))}
    </div>
  );
}

const CompanyGrid = memo(CompanyGridImpl);
export default CompanyGrid;
