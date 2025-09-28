import { NextResponse } from "next/server";

export async function POST(req: Request){
  const payload = await req.json().catch(()=>({}));
  const snapshot_id = `snap_${Date.now().toString(36)}`;
  return NextResponse.json({ snapshot_id, pngUrl: `/api/tmp/${snapshot_id}.png`, jsonUrl: `/api/tmp/${snapshot_id}.json`, payload });
}
