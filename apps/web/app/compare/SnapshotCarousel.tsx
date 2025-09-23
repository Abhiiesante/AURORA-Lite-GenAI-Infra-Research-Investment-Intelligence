"use client";
import React from 'react';

export type SnapshotItem = { id: string; dataUrl: string; title?: string; timestamp: string };

export function SnapshotCarousel({ items = [] }: { items?: SnapshotItem[] }){
  return (
    <div className="glass" style={{ padding:10, height:'100%', overflow:'hidden' }}>
      <div className="trend-label" style={{ marginBottom:8 }}>Snapshots</div>
      {items.length === 0 ? (
        <div className="trend-label" style={{ opacity:0.8 }}>No snapshots yet — click Save or Export.</div>
      ) : (
        <div style={{ display:'flex', gap:10, overflowX:'auto' }}>
          {items.map(s => (
            <div key={s.id} className="glass" style={{ minWidth:160, padding:6, borderRadius:8 }}>
              <div className="trend-label" style={{ fontSize:12, opacity:0.85, marginBottom:6 }}>{s.title || 'Snapshot'}</div>
              <img src={s.dataUrl} alt={s.title||'snapshot'} style={{ display:'block', width:148, height:84, objectFit:'cover', borderRadius:6, border:'1px solid rgba(255,255,255,0.12)' }} />
              <div className="trend-label" style={{ fontSize:11, opacity:0.65, marginTop:6 }}>{new Date(s.timestamp).toLocaleTimeString()}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
