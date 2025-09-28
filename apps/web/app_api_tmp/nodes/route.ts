import { NextResponse } from "next/server";

export async function GET() {
  const nodes = Array.from({ length: 200 }, (_, i) => ({
    id: `n${i}`,
    x: +(Math.random() * 4 - 2).toFixed(2),
    y: +(Math.random() * 2 - 1).toFixed(2),
    z: +(Math.random() * 4 - 2).toFixed(2),
    score: +(Math.random() * 100).toFixed(2),
    meta: { label: `Node ${i}` }
  }));
  const clusters = [
    { id: "c1", nodes: nodes.slice(0, 40).map(n => n.id), label: "AI Infra" },
    { id: "c2", nodes: nodes.slice(40, 100).map(n => n.id), label: "Data Apps" }
  ];
  return NextResponse.json({ nodes, clusters }, { headers: { ETag: 'W/"nodes-v1"' } });
}
