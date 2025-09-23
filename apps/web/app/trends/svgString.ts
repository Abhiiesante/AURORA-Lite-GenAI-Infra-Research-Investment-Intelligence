import type { SvgPoint, SvgMarker } from './exportSvg';

export function buildSvgString(opts: {
  width: number;
  height: number;
  points: SvgPoint[];
  lasso?: { x0:number; y0:number; x1:number; y1:number } | null;
  markers?: SvgMarker[];
  title?: string;
  asOf?: string;
}): string {
  const { width, height, points, lasso, markers = [], title = 'Trends Export', asOf } = opts;
  const w = Math.max(1, Math.floor(width));
  const h = Math.max(1, Math.floor(height));

  const selected = points.filter(p=>p.selected);
  const compares = points.filter(p=>p.compare).slice(0, 3);

  const lassoRect = lasso ? {
    x: Math.min(lasso.x0, lasso.x1),
    y: Math.min(lasso.y0, lasso.y1),
    width: Math.abs(lasso.x1 - lasso.x0),
    height: Math.abs(lasso.y1 - lasso.y0),
  } : null;

  const xmlEsc = (s: string) => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

  const markerEls = markers.map((m, i) => {
    const x = Math.round(m.t * w);
    const y = h - 28;
    const size = 8;
    const label = m.label ? xmlEsc(m.label) : `m${i+1}`;
    return `
      <g opacity="0.9">
        <polygon points="${x},${y} ${x-size},${y+size*1.6} ${x+size},${y+size*1.6}" fill="#FFD580" />
        <text x="${x}" y="${y+size*2.2}" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="10" fill="#e4e2dd">${label}</text>
      </g>
    `;
  }).join('\n');

  const pointEls = [...selected, ...compares].map((p) => {
    const r = p.selected ? 6 : 5;
    const stroke = p.selected ? '#00F0FF' : '#8BE9FF';
    const fill = 'none';
    const label = xmlEsc(p.label || p.id);
    const lx = Math.min(w - 8, Math.max(8, p.x + 10));
    const ly = Math.min(h - 8, Math.max(12, p.y - 10));
    return `
      <g>
        <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${r}" stroke="${stroke}" stroke-width="1.5" fill="${fill}" />
        <line x1="${p.x.toFixed(1)}" y1="${p.y.toFixed(1)}" x2="${lx}" y2="${ly}" stroke="${stroke}" stroke-width="1" opacity="0.8" />
        <rect x="${lx}" y="${ly-12}" rx="4" ry="4" width="${Math.max(40, label.length*6)}" height="18" fill="rgba(0,0,0,0.5)" />
        <text x="${lx+6}" y="${ly+2}" font-family="Inter, system-ui, sans-serif" font-size="11" fill="#e4e2dd">${label}</text>
      </g>
    `;
  }).join('\n');

  const lassoEl = lassoRect ? `
    <rect x="${lassoRect.x.toFixed(1)}" y="${lassoRect.y.toFixed(1)}" width="${lassoRect.width.toFixed(1)}" height="${lassoRect.height.toFixed(1)}"
      fill="rgba(0,240,255,0.08)" stroke="rgba(0,240,255,0.8)" stroke-dasharray="4 4" stroke-width="1" />
  ` : '';

  const footer = `
    <g opacity="0.9">
      <text x="12" y="${h-10}" font-family="Inter, system-ui, sans-serif" font-size="10" fill="#bdbab0">${xmlEsc(title)}${asOf ? ' — ' + xmlEsc(asOf) : ''}</text>
    </g>
  `;

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <defs>
    <style>
      @media (prefers-color-scheme: dark){ .bg { fill: #0a0b10; } }
    </style>
  </defs>
  <rect class="bg" x="0" y="0" width="${w}" height="${h}" fill="#0a0b10" />
  ${lassoEl}
  ${pointEls}
  ${markerEls}
  ${footer}
</svg>`;
  return svg;
}
