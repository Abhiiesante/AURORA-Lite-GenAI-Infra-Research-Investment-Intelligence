"use client";
import { useMemo, useState } from "react";

export function ForecastWidget(){
  const [growth, setGrowth] = useState(40); // %
  const [margin, setMargin] = useState(25); // %
  const [discount, setDiscount] = useState(12); // %
  const value = useMemo(()=>{
    // toy model: value ~ (growth * margin) / discount
    return Math.round(((growth/100)*(margin/100))/Math.max(0.01, discount/100) * 100) / 100;
  }, [growth, margin, discount]);
  return (
    <div>
      <div className="row" style={{ gap:12 }}>
        <label style={{ fontSize:12 }}>Growth {growth}%
          <input aria-label="Growth" type="range" min={0} max={100} value={growth} onChange={e=> setGrowth(parseInt(e.target.value))} />
        </label>
        <label style={{ fontSize:12 }}>Margin {margin}%
          <input aria-label="Margin" type="range" min={0} max={100} value={margin} onChange={e=> setMargin(parseInt(e.target.value))} />
        </label>
        <label style={{ fontSize:12 }}>Discount {discount}%
          <input aria-label="Discount" type="range" min={1} max={30} value={discount} onChange={e=> setDiscount(parseInt(e.target.value))} />
        </label>
      </div>
      <div className="glass" style={{ marginTop:8, padding:8, fontSize:14 }}>Scenario score: <b>{value}</b></div>
      {/* sensitivity grid */}
      <div style={{ marginTop:8 }}>
        <div style={{ fontSize:12, opacity:0.8, marginBottom:4 }}>Sensitivity (growth × margin)</div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(5, 1fr)", gap:4 }}>
          {[10,25,40,60,80].map(g=> [10,20,30,40,50].map(m=>{
            const v = Math.round(((g/100)*(m/100))/Math.max(0.01, discount/100) * 100) / 100;
            const active = g===growth && m===margin;
            return <div key={`${g}-${m}`} style={{ padding:6, textAlign:"center", borderRadius:6, border:"1px solid rgba(255,255,255,0.1)", background: active? "rgba(34,211,238,0.2)":"transparent" }}>{v}</div>;
          }))}
        </div>
      </div>
    </div>
  );
}
