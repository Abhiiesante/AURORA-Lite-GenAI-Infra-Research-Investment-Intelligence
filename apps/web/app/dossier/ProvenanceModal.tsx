"use client";

export function ProvenanceModal({ onClose, bundle }: { onClose: ()=>void; bundle?: any }){
  const sample = bundle || {
    pipeline_version: "v1",
    snapshot_hash: "mroot:abc123",
    retrieval_trace: [
      { id: "s1", source: "edgar-8k", url: "https://www.sec.gov/ixviewer" },
      { id: "s2", source: "press-2024", url: "https://example.com" },
    ]
  };
  return (
    <div role="dialog" aria-modal className="cmdk-overlay" onClick={onClose}>
      <div className="cmdk-panel" onClick={e=>e.stopPropagation()} style={{ gridTemplateColumns: "1fr" }}>
        <header className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Provenance</h3>
          <button onClick={onClose}>Close</button>
        </header>
        <div className="glass" style={{ padding: 12 }}>
          <div style={{ fontSize: 12, opacity: 0.85 }}>Pipeline: <b>{sample.pipeline_version}</b> · Snapshot: <b>{sample.snapshot_hash}</b></div>
          <ul style={{ marginTop: 8 }}>
            {sample.retrieval_trace?.map((r:any)=> (
              <li key={r.id} style={{ fontSize: 14 }}>
                {r.source} — <a href={r.url} target="_blank" rel="noreferrer">view raw</a>
                <span style={{ marginLeft: 8 }}>
                  <button className="magnetic" style={{ padding:"4px 8px", borderRadius: 8, marginRight: 6 }}>Cite</button>
                  <button className="magnetic" style={{ padding:"4px 8px", borderRadius: 8 }}>Flag</button>
                </span>
              </li>
            ))}
          </ul>
          <div className="row" style={{ marginTop: 8 }}>
            <button className="magnetic" onClick={()=> { navigator.clipboard?.writeText(JSON.stringify(sample, null, 2)); }}>Copy bundle JSON</button>
          </div>
        </div>
      </div>
    </div>
  );
}
