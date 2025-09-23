import { NextResponse } from "next/server";

export async function GET(_req: Request, { params }: { params: { id: string } }){
  const cps = [
    { date: '2025-05-08', type: 'spike', confidence: 0.92, reason: 'Major funding announcement; multiple press items' },
    { date: '2025-06-14', type: 'sharp_increase', confidence: 0.86, reason: 'Hiring surge in infra roles' }
  ];
  return NextResponse.json({ topic_id: params.id, change_points: cps });
}
