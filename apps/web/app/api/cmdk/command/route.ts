import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const jobId = Math.random().toString(36).slice(2);
  const estimatedSeconds = 2;
  return NextResponse.json({ jobId, statusUrl: `/api/cmdk/command/${jobId}`, estimatedSeconds, received: body });
}
