import { NextRequest, NextResponse } from 'next/server';

export async function POST(_req: NextRequest, { params }: { params: { id: string } }){
  const id = params.id;
  const snapshot_id = Math.random().toString(36).slice(2,10);
  const pngUrl = `/api/compare/${id}/snapshot/${snapshot_id}.png`;
  const jsonUrl = `/api/compare/${id}/snapshot/${snapshot_id}.json`;
  const signed_hash = `sha256:${snapshot_id}`;
  return NextResponse.json({ pngUrl, jsonUrl, snapshot_id, signed_hash });
}
