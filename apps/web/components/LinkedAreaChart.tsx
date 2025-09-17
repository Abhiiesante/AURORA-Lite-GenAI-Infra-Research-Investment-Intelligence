"use client";
import React, { useMemo } from "react";
import dynamic from "next/dynamic";
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, loading: () => <div className="skeleton" style={{ height: 240 }} /> });
import { useLinkedStore } from "@/app/linkedStore";

type Series = { id: string; name: string; color: string; values: number[] };

function makeSeries(): Series[] {
  const base = Array.from({ length: 24 }, (_, i) => i);
  return [
    { id: "A", name: "Cluster A", color: "#00f0ff", values: base.map((i) => 40 + Math.sin(i / 2) * 14 + (i % 3)) },
    { id: "B", name: "Cluster B", color: "#b266ff", values: base.map((i) => 28 + Math.cos(i / 3) * 10) },
    { id: "C", name: "Cluster C", color: "#ffb86b", values: base.map((i) => 18 + Math.sin(i / 4 + 0.6) * 8) },
    { id: "D", name: "Cluster D", color: "#e6eefc", values: base.map((i) => 12 + Math.cos(i / 5 + 0.3) * 6) },
  ];
}

export default function LinkedAreaChart() {
  const selected = useLinkedStore((s) => s.selected);
  const setHover = useLinkedStore((s) => s.setHover);
  const series = useMemo(() => makeSeries(), []);
  const prefersReduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const data = series.map((s: Series) => ({
    x: Array.from({ length: s.values.length }, (_, i) => i),
    y: s.values,
    type: "scatter",
    mode: "lines",
    name: s.name,
    fill: "tozeroy" as const,
    hoverinfo: "x+y+name",
    line: { color: s.color, width: selected && selected !== s.id ? 1 : 2.5 },
    opacity: selected && selected !== s.id ? 0.35 : 0.95,
    customdata: Array(s.values.length).fill(s.id),
  }));

  const layout: any = {
    margin: { l: 28, r: 14, t: 10, b: 24 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    xaxis: { color: "#9fb0d2", gridcolor: "rgba(230,238,252,0.08)" },
    yaxis: { color: "#9fb0d2", gridcolor: "rgba(230,238,252,0.08)" },
    showlegend: true,
    legend: { font: { color: "#e6eefc" } },
  };

  if (prefersReduced) {
    return <div className="glass" style={{ padding: 12, minHeight: 240 }} aria-label="Trends chart placeholder" />;
  }
  return (
    <div className="glass" style={{ padding: 8 }}>
      <Plot
        data={data as any}
        layout={layout as any}
        style={{ width: "100%", height: 240 }}
        config={{ displayModeBar: false, responsive: true }}
        onHover={(ev: any) => {
          const id = ev?.points?.[0]?.customdata as string | undefined;
          if (id) setHover(id);
        }}
        onUnhover={() => setHover(null)}
        onClick={(ev: any) => {
          const id = ev?.points?.[0]?.customdata as string | undefined;
          if (id) useLinkedStore.getState().setSelected(id);
        }}
      />
    </div>
  );
}
