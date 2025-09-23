import { NextRequest, NextResponse } from 'next/server';

type Session = {
  compare_id: string;
  companies: string[];
  weights: Record<string, number>;
  composite_scores: Record<string, number>;
  timestamp: string;
};

const store: Map<string, Session> = (global as any).__COMPARE_STORE__ || new Map();
(global as any).__COMPARE_STORE__ = store;

function computeComposite(weights: Record<string, number>, metrics: Record<string, number>){
  const sum = Object.values(weights).reduce((s,n)=> s + (n||0), 0) || 1;
  let score = 0;
  for (const [k,w] of Object.entries(weights)){
    const v = metrics[k] ?? 0.5; // dev stub value
    score += (w/sum) * v;
  }
  return Math.max(0, Math.min(1, score));
}

export async function POST(req: NextRequest){
  // dev-only in-memory session
  const body = await req.json();
  const companies: string[] = body?.companies || [];
  const weights: Record<string, number> = body?.weights || { revenue_growth: 0.4, arr: 0.2, dev_velocity: 0.25, gross_margin: 0.15 };
  const id = Math.random().toString(36).slice(2, 10);
  const composite_scores: Record<string, number> = {};
  for (const cid of companies){
    composite_scores[cid] = computeComposite(weights, {});
  }
  const session: Session = { compare_id: id, companies, weights, composite_scores, timestamp: new Date().toISOString() };
  store.set(id, session);
  return NextResponse.json({ compare_id: id, compare_session: session });
}
