"use client";
export type Company = {
  id: string;
  name: string;
  logo?: string;
  metrics: Record<string, number>;
};

export type CompareSession = {
  compare_id: string;
  companies: string[];
  weights: Record<string, number>;
  composite_scores: Record<string, number>;
  timestamp: string;
  snapshot_hash?: string;
};

export function getBaseUrl(){
  return process.env.NEXT_PUBLIC_API_URL || '';
}

export async function postCompare(body: { companies: string[]; weights?: Record<string, number> }): Promise<{ compare_id: string; compare_session?: CompareSession }>{
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/compare`, { method:'POST', headers:{ 'content-type':'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`compare create failed ${res.status}`);
  return res.json();
}

export async function getCompare(id: string): Promise<{ compare_session: CompareSession }>{
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/compare/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`compare get failed ${res.status}`);
  return res.json();
}

export async function postWeight(id: string, body: { metric: string; delta: number }): Promise<{ composite_scores: Record<string, number>; weights: Record<string, number> }>{
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/compare/${encodeURIComponent(id)}/weight`, { method:'POST', headers:{ 'content-type':'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`compare weight failed ${res.status}`);
  return res.json();
}

export async function postSnapshot(id: string): Promise<{ pngUrl: string; jsonUrl: string; snapshot_id: string; signed_hash: string }>{
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/compare/${encodeURIComponent(id)}/snapshot`, { method:'POST' });
  if (!res.ok) throw new Error(`compare snapshot failed ${res.status}`);
  return res.json();
}
