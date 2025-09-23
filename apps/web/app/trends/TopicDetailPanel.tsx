"use client";
import React from "react";

export function TopicDetailPanel({ topic, onDrill }: { topic: any; onDrill: ()=>void }){
  if (!topic) return (
    <div className="glass" style={{ padding: 16 }}>
      <div style={{ opacity: 0.7 }}>Select a topic</div>
    </div>
  );
  return (
    <div className="glass" style={{ padding: 16, display: 'grid', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div>
          <div className="title-orbitron" style={{ fontSize: 18 }}>{topic.label}</div>
          <div className="numeric-sg" style={{ opacity: 0.8 }}>Momentum: {(topic.momentum*100|0)}%</div>
        </div>
        <button style={{ background: 'rgba(255,255,255,0.1)', border:'1px solid rgba(255,255,255,0.2)', color:'var(--starlight)', borderRadius:6, padding:'8px 12px', cursor:'pointer' }}>Save</button>
      </div>
      <div>
        <div style={{ fontSize:12, opacity:0.7, marginBottom:6 }}>Top terms</div>
        <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
          {(topic.top_terms||[]).slice(0,8).map((t:any,i:number)=>(
            <span key={i} className="trend-label" style={{ background:'rgba(255,255,255,0.08)', border:'1px solid rgba(255,255,255,0.16)', padding:'6px 8px', borderRadius:14 }}>{t.term}</span>
          ))}
        </div>
      </div>
      <div>
        <div style={{ fontSize:12, opacity:0.7, marginBottom:6 }}>Top sources</div>
        <div style={{ display:'grid', gap:6 }}>
          {(topic.top_sources||[]).slice(0,5).map((s:any,i:number)=>(
            <a key={i} href={s.url} target="_blank" rel="noreferrer" style={{ color:'var(--aurora-cyan)', fontSize:13, textDecoration:'none' }}>{s.url}</a>
          ))}
        </div>
      </div>
      <div>
        <div style={{ fontSize:12, opacity:0.7, marginBottom:6 }}>Impacted companies</div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap:8 }}>
          {(topic.impacted_companies||[]).slice(0,6).map((c:any,i:number)=>(
            <div key={i} className="glass" style={{ padding:8, borderRadius:8 }}>
              <div className="trend-label">{c.company_id}</div>
              <div className="numeric-sg" style={{ fontSize:12, opacity:0.8 }}>Impact {Math.round((c.impact_score||0)*100)}%</div>
            </div>
          ))}
        </div>
      </div>
      <button onClick={onDrill} style={{ background:'var(--aurora-cyan)', color:'#05070A', border:'none', padding:'10px 12px', borderRadius:6, cursor:'pointer' }}>Drill into drivers</button>
    </div>
  );
}
