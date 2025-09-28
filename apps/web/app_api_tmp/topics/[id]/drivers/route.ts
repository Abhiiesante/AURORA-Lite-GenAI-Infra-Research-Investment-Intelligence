import { NextResponse } from "next/server";

export async function GET(_req: Request, { params }: { params: { id: string } }){
  const drivers = {
    top_sources: [
      { url: 'https://techcrunch.com/rag-shift', score: 0.93, retrieved_at: new Date().toISOString() },
      { url: 'https://arxiv.org/abs/xxx', score: 0.88 }
    ],
    top_companies: [
      { company_id: 'company:pinecone', impact_score: 0.88 },
      { company_id: 'company:weaviate', impact_score: 0.72 }
    ],
    provenance_bundle: {
      snapshot_hash: `sha256:${Math.random().toString(36).slice(2)}`,
      pipeline_version: 'trends-v1.0',
      created_at: new Date().toISOString()
    }
  };
  return NextResponse.json({ topic_id: params.id, ...drivers });
}
