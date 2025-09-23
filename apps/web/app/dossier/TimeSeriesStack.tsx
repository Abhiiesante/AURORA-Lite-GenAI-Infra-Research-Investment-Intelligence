"use client";
import { useEffect, useMemo, useRef, useState } from "react";

type Series = { date: string; value: number }[];
export function TimeSeriesStack({
  revenue,
  commits,
  jobs,
}: { revenue?: Series; commits?: Series; jobs?: Series }){
  const [selection, setSelection] = useState(null as any);
  const svgRef = useRef(null as any);
  const [showTable, setShowTable] = useState(false);
  const width = 640; const height = 220; const pad = 28;

  // tiny scales without d3 to keep deps minimal
  const points = useMemo(() => {
    const toPts = (s?: Series) => (s||[]).map((d,i,arr)=>{
      const x = pad + (i * (width - pad*2)) / Math.max(1,(arr.length-1));
      const y = height - pad - (d.value * (height - pad*2)) / Math.max(1, Math.max(...(s||[]).map(t=>t.value), 1));
      return [x,y] as const;
    });
    return { r: toPts(revenue), c: toPts(commits), j: toPts(jobs) };
  }, [revenue, commits, jobs]);

  function path(pts: readonly (readonly [number,number])[], smooth=false){
    if (!pts.length) return "";
    if (!smooth) return `M ${pts.map(p=>p.join(",")).join(" L ")}`;
    // simple cardinal-ish smoothing
    let d = `M ${pts[0][0]},${pts[0][1]}`;
    for (let i=1;i<pts.length;i++){
      const p0 = pts[i-1], p1 = pts[i];
      const mx = (p0[0]+p1[0])/2; const my = (p0[1]+p1[1])/2;
      d += ` Q ${p0[0]},${p0[1]} ${mx},${my}`;
    }
    d += ` T ${pts[pts.length-1][0]},${pts[pts.length-1][1]}`;
    return d;
  }

  function onDragStart(e: React.MouseEvent){
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left; setSelection({ x0:x, x1:x });
  function move(ev: MouseEvent){ const x = ev.clientX - rect.left; setSelection((sel: any)=> sel? { ...sel, x1:x } : null); }
    function up(){ window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up); }
    window.addEventListener('mousemove', move); window.addEventListener('mouseup', up);
  }

  const sel = selection && { x: Math.min(selection.x0, selection.x1), w: Math.abs(selection.x1 - selection.x0) };

  useEffect(() => {
    const svg = svgRef.current as SVGSVGElement | null;
    if (!svg) return;
    const onExport = () => exportSVGAsPNG(svg, "timeseries.png");
    const onToggle = () => setShowTable((v: any)=> !v);
    svg.addEventListener('ts-export' as any, onExport);
    svg.addEventListener('ts-toggle-table' as any, onToggle);
    return () => { svg.removeEventListener('ts-export' as any, onExport); svg.removeEventListener('ts-toggle-table' as any, onToggle); };
  }, [svgRef.current]);

  return (
    <>
    <svg ref={svgRef} role="img" width={width} height={height} style={{ width:"100%" }} onMouseDown={onDragStart} aria-label="Time series: revenue, commits, jobs">
      <rect x={0} y={0} width={width} height={height} fill="transparent" />
      {/* axes */}
      <line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="#6b72804d" />
      <line x1={pad} y1={pad} x2={pad} y2={height-pad} stroke="#6b72804d" />
      {/* series */}
      <path d={path(points.r, true)} stroke="#22d3ee" fill="none" strokeWidth={2} />
      <path d={path(points.c, true)} stroke="#a78bfa" fill="none" strokeWidth={2} />
      <path d={path(points.j, true)} stroke="#f472b6" fill="none" strokeWidth={2} />
      {sel && <rect x={sel.x} y={pad} width={sel.w} height={height-pad*2} fill="#22d3ee22" stroke="#22d3ee55" />}
      {/* legend */}
      <g fontSize={12} fill="#cbd5e1" aria-hidden>
        <text x={pad} y={16}>Revenue</text>
        <text x={pad+90} y={16}>Commits</text>
        <text x={pad+170} y={16}>Jobs</text>
      </g>
    </svg>
    {showTable && (
      <div style={{ marginTop: 8 }}>
        <table role="table" aria-label="Time series data" style={{ width:"100%", fontSize:12 }}>
          <thead><tr><th>Date</th><th>Revenue</th><th>Commits</th><th>Jobs</th></tr></thead>
          <tbody>
            {(revenue||[]).map((r,i)=> (
              <tr key={i}><td>{r.date}</td><td>{r.value}</td><td>{commits?.[i]?.value ?? ''}</td><td>{jobs?.[i]?.value ?? ''}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
    </>
  );
}

export function exportSVGAsPNG(svg: SVGSVGElement, fileName: string){
  const xml = new XMLSerializer().serializeToString(svg);
  const svg64 = btoa(unescape(encodeURIComponent(xml)));
  const image64 = `data:image/svg+xml;base64,${svg64}`;
  const img = new Image();
  img.onload = function(){
    const canvas = document.createElement('canvas');
    canvas.width = svg.viewBox.baseVal.width || svg.clientWidth; canvas.height = svg.viewBox.baseVal.height || svg.clientHeight;
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    ctx.drawImage(img,0,0);
    const link = document.createElement('a'); link.download = fileName; link.href = canvas.toDataURL('image/png'); link.click();
  };
  img.src = image64;
}
