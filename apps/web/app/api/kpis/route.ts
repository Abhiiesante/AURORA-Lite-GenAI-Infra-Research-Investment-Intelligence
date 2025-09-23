import { NextResponse } from "next/server";

export async function GET() {
  const body = {
    signalScore: 74,
    marketMomentum: "+12.4%",
    topAlert: { title: "Vector DB hiring surge", severity: "high" },
    dealPipeline: 8,
    trendSeries: Array.from({ length: 24 }, () => Math.round(50 + Math.random() * 20)),
  };
  return NextResponse.json(body, { headers: { ETag: 'W/"kpis-v1"' } });
}
