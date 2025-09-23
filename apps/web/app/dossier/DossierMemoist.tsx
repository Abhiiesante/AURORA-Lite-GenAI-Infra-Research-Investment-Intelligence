"use client";
import { useEffect, useState } from "react";
import { sfx } from "../sfx";

export function DossierMemoist({ companyId, onClose, onComplete }: { companyId: string; onClose: ()=>void; onComplete: (memo:any)=>void }){
  const [template, setTemplate] = useState("onepager");
  const [loading, setLoading] = useState(false);
  const [memo, setMemo] = useState(null as any);

  async function generate(){
    setLoading(true); sfx.open();
    try{
      const res = await fetch(`/api/memo/generate`, { method: "POST", body: JSON.stringify({ companyId, template }) });
      const data = await res.json();
      setMemo(data); onComplete(data); sfx.confirm();
    } finally {
      setLoading(false);
    }
  }

  useEffect(()=>{ generate(); }, []);

  return (
    <div role="dialog" aria-modal className="cmdk-overlay" onClick={onClose}>
      <div className="cmdk-panel" onClick={e=>e.stopPropagation()} style={{ gridTemplateColumns: "1fr" }}>
        <header className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Generate Memo</h3>
          <button onClick={onClose}>Close</button>
        </header>
        <div className="row" style={{ gap: 8 }}>
          <label style={{ fontSize: 12 }}>Template
            <select value={template} onChange={e=> setTemplate(e.target.value)}>
              <option value="onepager">One-Pager</option>
              <option value="investment-thesis">Investment Thesis</option>
              <option value="technical-dossier">Technical Dossier</option>
            </select>
          </label>
          <button className="magnetic" onClick={generate} disabled={loading}>
            {loading ? "Generating…" : "Regenerate"}
          </button>
        </div>
        <div className="glass" style={{ padding: 12, minHeight: 180, marginTop: 8 }}>
          {loading && <div>Working…</div>}
          {memo && (
            <div>
              <p><b>Thesis:</b> {memo.thesis}</p>
              <ul>
                {memo.bullets?.map((b:any)=> <li key={b.id}>{b.text} <small>({b.sources?.join(', ')})</small></li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
