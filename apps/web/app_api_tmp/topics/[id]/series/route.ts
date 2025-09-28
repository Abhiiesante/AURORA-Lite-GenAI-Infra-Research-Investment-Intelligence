import { NextResponse } from "next/server";

export async function GET(_req: Request, { params }: { params: { id: string } }){
  const { id } = params;
  const today = new Date();
  const series = Array.from({ length: 12 }).map((_, i) => {
    const d = new Date(today); d.setDate(d.getDate() - (11 - i) * 7);
    return { date: d.toISOString().slice(0,10), frequency: Math.round(20 + Math.random()*80), sentiment: +(Math.random()*0.4-0.2).toFixed(2), velocity: +(Math.random()*0.4).toFixed(2) };
  });
  return NextResponse.json({ topic_id: id, series });
}
