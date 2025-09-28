import { NextRequest, NextResponse } from 'next/server';

const store: Map<string, any> = (global as any).__COMPARE_STORE__ || new Map();

export async function GET(_req: NextRequest, { params }: { params: { id: string } }){
  const id = params.id;
  const session = store.get(id);
  if (!session){
    return new NextResponse('Not Found', { status: 404 });
  }
  return NextResponse.json({ compare_session: session });
}
