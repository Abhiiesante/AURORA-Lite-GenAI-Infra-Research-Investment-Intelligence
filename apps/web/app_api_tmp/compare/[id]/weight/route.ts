import { NextRequest, NextResponse } from 'next/server';

const store: Map<string, any> = (global as any).__COMPARE_STORE__ || new Map();

function computeComposite(weights: Record<string, number>, metrics: Record<string, number>){
  const sum = Object.values(weights).reduce((s,n)=> s + (n||0), 0) || 1;
  let score = 0;
  for (const [k,w] of Object.entries(weights)){
    const v = metrics[k] ?? 0.5;
    score += (w/sum) * v;
  }
  return Math.max(0, Math.min(1, score));
}

export async function POST(req: NextRequest, { params }: { params: { id: string } }){
  const id = params.id;
  const session = store.get(id);
  if (!session){
    return new NextResponse('Not Found', { status: 404 });
  }
  const body = await req.json();
  const metric = body?.metric as string;
  const delta = Number(body?.delta || 0);
  const weights: Record<string, number> = { ...session.weights, [metric]: Math.max(0, Math.min(1, (session.weights[metric] || 0) + delta)) };
  const composite_scores: Record<string, number> = {};
  for (const cid of session.companies){
    composite_scores[cid] = computeComposite(weights, {});
  }
  session.weights = weights;
  session.composite_scores = composite_scores;
  store.set(id, session);
  return NextResponse.json({ weights, composite_scores });
}
