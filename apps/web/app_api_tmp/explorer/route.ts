import { NextResponse } from "next/server";

let etag = "W/\"explorer-v1\"";

const sectors = ["tech", "healthcare", "finance", "energy", "retail"] as const;
type Sector = typeof sectors[number];

function random(seed: number) {
  let s = seed;
  return () => (s = (s * 1664525 + 1013904223) % 4294967296) / 4294967296;
}

export async function GET(req: Request) {
  const ifNoneMatch = req.headers.get("if-none-match");
  const url = new URL(req.url);
  const seed = Number(url.searchParams.get("seed") || 42);
  const count = Math.min(Number(url.searchParams.get("count") || 400), 1500);
  const rng = random(seed);

  const nodes = Array.from({ length: count }, (_, i) => {
    const sector = sectors[Math.floor(rng() * sectors.length)] as Sector;
    const signal = Math.round(rng() * 100);
    return {
      id: `n${i}`,
      name: `Company ${i}`,
      x: (rng() - 0.5) * 10,
      y: (rng() - 0.5) * 6,
      z: (rng() - 0.5) * 10,
      sector,
      signal,
      metrics: {
        hiring: Math.round(rng() * 1000),
        funding: Math.round(rng() * 500),
        partnerships: Math.round(rng() * 20),
        sentiment: Math.round((rng() * 200 - 100) * 10) / 10,
        freshness: rng(),
      },
    };
  });

  const edges = [] as Array<{ source: string; target: string; weight: number }>;
  for (let i = 0; i < count; i++) {
    const links = Math.floor(rng() * 4);
    for (let k = 0; k < links; k++) {
      const j = Math.floor(rng() * count);
      if (j !== i) edges.push({ source: nodes[i].id, target: nodes[j].id, weight: Math.round(rng() * 100) / 100 });
    }
  }

  const body = { nodes, edges, updatedAt: new Date().toISOString() };
  const nextEtag = 'W/"' + Buffer.from(JSON.stringify({ seed, count })).toString('base64').slice(0, 16) + '"';
  if (ifNoneMatch && ifNoneMatch === nextEtag) {
    return new NextResponse(null, { status: 304, headers: { ETag: nextEtag } as any });
  }
  etag = nextEtag;
  return NextResponse.json(body, { headers: { ETag: etag } as any });
}
