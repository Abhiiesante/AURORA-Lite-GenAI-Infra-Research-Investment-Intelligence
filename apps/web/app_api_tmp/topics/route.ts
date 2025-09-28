import { NextResponse } from "next/server";

export async function GET(req: Request){
  const url = new URL(req.url);
  const window = url.searchParams.get('window') || '90d';
  const topics = [
    { topic_id: 'topic:rag', label:'Retrieval-Augmented Generation', momentum: 0.82, trend_state:'rising', top_terms:[{term:'vector-db',score:0.9}], top_sources:[{url:'https://techcrunch.com/rag',score:0.93}], impacted_companies:[{company_id:'company:pinecone',impact_score:0.88}] },
    { topic_id: 'topic:vector-db', label:'Vector Databases', momentum: 0.74, trend_state:'rising', top_terms:[{term:'RAG',score:0.82}], top_sources:[{url:'https://example.com/vdb',score:0.9}], impacted_companies:[{company_id:'company:weaviate',impact_score:0.7}] },
    { topic_id: 'topic:agentic', label:'Agentic Systems', momentum: 0.31, trend_state:'stable' },
    { topic_id: 'topic:finetuning', label:'Fine-tuning', momentum: -0.12, trend_state:'declining' }
  ];
  return NextResponse.json({ window, topics });
}
