import { NextRequest, NextResponse } from "next/server";

function makeSvgDataUrl(label: string, w: number, h: number) {
  const fontSize = Math.max(10, Math.floor(h * 0.22));
  const svg = `<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#0b1220"/><stop offset="100%" stop-color="#071017"/></linearGradient></defs><rect width="100%" height="100%" fill="url(#g)"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="rgba(0,240,255,0.85)" font-family="Roboto Mono, monospace" font-size="${fontSize}">${label.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</text></svg>`;
  const encoded = encodeURIComponent(svg);
  return `data:image/svg+xml;charset=utf-8,${encoded}`;
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const entity = searchParams.get('entity') || 'entity';
  const size = (searchParams.get('size') || '160x96');
  const [w, h] = size.split('x').map((n) => parseInt(n, 10));
  const dataUrl = makeSvgDataUrl(entity, isFinite(w)? w:160, isFinite(h)? h:96);
  return NextResponse.json({ pngUrl: dataUrl, generatedAt: new Date().toISOString(), cacheHit: false, snapshot_id: entity, signed_hash: 'dev' });
}
