"use client";
import React from 'react';

export function ExplainBox({ leftName, rightName, leftScore, rightScore }: { leftName?: string; rightName?: string; leftScore: number; rightScore: number }){
  const lead = leftScore > rightScore ? leftName : rightName;
  const diff = Math.abs(leftScore - rightScore);
  const pct = Math.round(diff * 100);
  return (
    <div className="glass" style={{ padding:12 }}>
      <div className="trend-label" style={{ marginBottom:8 }}>Explain</div>
      <div className="trend-label" style={{ opacity:0.85 }}>
        {lead ? `${lead} leads by ~${pct}% — top drivers: dev_velocity, ARR.` : 'Add companies to compare.'}
      </div>
    </div>
  );
}
