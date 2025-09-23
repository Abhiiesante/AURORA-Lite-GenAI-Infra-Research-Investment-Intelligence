export function buildCompareSvg(opts: {
  width: number;
  height: number;
  title: string;
  asOf: string;
  leftName?: string;
  rightName?: string;
  leftScore: number;
  rightScore: number;
  weights: Record<string, number>;
}){
  const { width, height, title, asOf, leftName='—', rightName='—', leftScore, rightScore, weights } = opts;
  const pad = 24;
  const headerY = pad + 18;
  const colY = headerY + 28;
  const textColor = '#c9d6ff';
  const subColor = '#93a2d8';
  const wCol = Math.max(220, Math.min(380, width * 0.32));
  const weightX = width - wCol - pad;
  const lines = Object.entries(weights).map(([k,v]) => `<tspan x="${weightX}" dy="18">${escapeXml(k)} · ${(v*100|0)}%</tspan>`).join('');
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <linearGradient id="g1" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#0b1020"/>
      <stop offset="1" stop-color="#0e1630"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="${width}" height="${height}" fill="url(#g1)"/>
  <text x="${pad}" y="${headerY}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto" font-size="18" fill="${textColor}">${escapeXml(title)}</text>
  <text x="${pad}" y="${headerY+18}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto" font-size="12" fill="${subColor}">as of ${escapeXml(asOf)}</text>
  <text x="${pad}" y="${colY}" font-size="16" fill="${textColor}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto">${escapeXml(leftName)}</text>
  <text x="${pad}" y="${colY+22}" font-size="28" fill="${textColor}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto">${(leftScore*100|0)}%</text>
  <text x="${pad+180}" y="${colY}" font-size="16" fill="${textColor}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto">${escapeXml(rightName)}</text>
  <text x="${pad+180}" y="${colY+22}" font-size="28" fill="${textColor}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto">${(rightScore*100|0)}%</text>
  <text x="${weightX}" y="${colY}" font-size="14" fill="${textColor}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto">Weights</text>
  <text x="${weightX}" y="${colY+20}" font-size="12" fill="${subColor}" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto">${lines}</text>
</svg>`;
}

function escapeXml(s: string){
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
