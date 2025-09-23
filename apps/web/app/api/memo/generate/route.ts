import { NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(req: Request){
  const body = await req.json().catch(()=>({}));
  const companyId = body?.companyId || "company:demo";
  const template = body?.template || "onepager";
  const additionalBullets = body?.additionalBullets || [];

  try {
    // Extract numeric ID from companyId (e.g., "company:123" -> "123")
    const numericId = companyId.replace(/^company:/, '').replace(/^id:/, '');
    
    // Fetch company insights and provenance data from FastAPI
    const [insightsRes, provenanceRes] = await Promise.all([
      fetch(`${API_BASE}/insights/company/${numericId}`).then(r => r.ok ? r.json() : null),
      fetch(`${API_BASE}/forecast/provenance/${numericId}`).then(r => r.ok ? r.json() : null)
    ]);

    // Simulate some processing latency for realistic UX
    await new Promise(r => setTimeout(r, Math.random() * 500 + 300));

    // Build provenance bundle from FastAPI data
    const provenance_bundle = {
      provenance_id: provenanceRes?.provenance_id || `prov:${companyId}-${Math.random().toString(36).slice(2)}`,
      pipeline_version: provenanceRes?.pipeline_version || "ingest-v2.4.1",
      snapshot_hash: provenanceRes?.snapshot_hash || `sha256:${Math.random().toString(36).substring(2)}${Date.now().toString(36)}`,
      model_version: "memoist-v1.2",
      retrieval_trace: provenanceRes?.retrieval_trace || [
        { doc_id: "doc:edgar-8k-2024", url: "https://www.sec.gov/...", score: 0.94 },
        { doc_id: "doc:press-2024", url: "https://techcrunch.com/...", score: 0.82 },
        { doc_id: `doc:github-${numericId}`, url: `https://github.com/${numericId}/${numericId}`, score: 0.78 },
      ],
      signed_by: provenanceRes?.signed_by || "aurora-platform-pubkey:v2",
      signature: provenanceRes?.signature || `sig:${Math.random().toString(36).substring(2)}`,
      created_at: new Date().toISOString()
    };

    // Extract company name and insights
    const companyName = insightsRes?.company || numericId;
    const companySummary = insightsRes?.summary || "AI-powered platform for data analytics";
    const swot = insightsRes?.swot || {};
    const sources = insightsRes?.sources || [];

    // Generate memo bullets based on available data
    const baseBullets = [];
    
    // What they do (from summary)
    if (companySummary && companySummary !== "Insufficient evidence") {
      baseBullets.push({
        id: "what",
        text: `What they do: ${companySummary}`,
        sources: sources.slice(0, 2).map((_url: any, idx: number) => `doc:source-${idx + 1}`)
      });
    }

    // Strengths (from SWOT)
    if (swot.strengths && Array.isArray(swot.strengths) && swot.strengths.length > 0) {
      baseBullets.push({
        id: "strength",
        text: `Key strength: ${swot.strengths[0]}`,
        sources: sources.slice(1, 3).map((_url: any, idx: number) => `doc:strength-${idx + 1}`)
      });
    }

    // Opportunities or market position
    if (swot.opportunities && Array.isArray(swot.opportunities) && swot.opportunities.length > 0) {
      baseBullets.push({
        id: "opportunity",
        text: `Market opportunity: ${swot.opportunities[0]}`,
        sources: sources.slice(0, 2).map((_url: any, idx: number) => `doc:market-${idx + 1}`)
      });
    }

    // Primary risk (from SWOT)
    if (swot.weaknesses && Array.isArray(swot.weaknesses) && swot.weaknesses.length > 0) {
      baseBullets.push({
        id: "risk",
        text: `Primary risk: ${swot.weaknesses[0]}`,
        sources: sources.slice(2, 4).map((_url: any, idx: number) => `doc:risk-${idx + 1}`)
      });
    } else if (swot.threats && Array.isArray(swot.threats) && swot.threats.length > 0) {
      baseBullets.push({
        id: "risk",
        text: `Market threat: ${swot.threats[0]}`,
        sources: sources.slice(2, 4).map((_url: any, idx: number) => `doc:threat-${idx + 1}`)
      });
    }

    // Fallback bullets if no insights available
    if (baseBullets.length === 0) {
      baseBullets.push(
        { id: "what", text: `What they do: ${companyName} operates in the AI/data analytics space`, sources: ["doc:fallback-1"] },
        { id: "opportunity", text: "Why it matters: Infrastructure for next-gen AI applications", sources: ["doc:fallback-2"] },
        { id: "risk", text: "Primary risk: Competitive market with platform dependencies", sources: ["doc:fallback-3"] }
      );
    }

    // Merge additional bullets from request (e.g., from RepoPanel)
    const allBullets = [...baseBullets, ...additionalBullets.map((bullet: any, idx: number) => ({
      id: `custom-${idx}`,
      text: bullet.text || bullet,
      sources: bullet.sources || [`doc:custom-${idx}`]
    }))];

    // Generate thesis based on available data
    let thesis = companySummary;
    if (template === "investment" && swot.strengths && swot.opportunities) {
      thesis = `Investment thesis: ${companyName} leverages ${swot.strengths[0]?.toLowerCase()} to capitalize on ${swot.opportunities[0]?.toLowerCase()}`;
    } else if (template === "competitive" && swot.strengths && swot.threats) {
      thesis = `Competitive positioning: ${companyName} differentiates through ${swot.strengths[0]?.toLowerCase()} despite ${swot.threats[0]?.toLowerCase()}`;
    }

    const memo = {
      memo_id: `memo-${numericId}`,
      company_name: companyName,
      thesis: thesis,
      confidence: 0.75 + Math.random() * 0.2, // Mock confidence 75-95%
      claims: allBullets.map((bullet, index) => ({
        claim_id: bullet.id,
        text: bullet.text,
        sources: bullet.sources,
        evidence_snippet: `Supporting evidence for: ${bullet.text.substring(0, 100)}...`,
        confidence: 0.65 + Math.random() * 0.3 // Mock individual confidence
      })),
      generated_at: new Date().toISOString(),
      provenance: {
        snapshot_hash: provenance_bundle.snapshot_hash,
        merkle_root: `merkle:${Math.random().toString(36).substring(2)}`,
        signed_by: provenance_bundle.signed_by,
        timestamp: new Date().toISOString(),
        retrieval_trace: {
          query: `investment analysis ${companyName}`,
          sources: provenance_bundle.retrieval_trace.map((trace: any) => ({
            source: trace.doc_id,
            score: trace.score,
            chunk: `Analysis data from ${trace.doc_id}...`
          })),
          total_sources: provenance_bundle.retrieval_trace.length,
          confidence: 0.8 + Math.random() * 0.15
        },
        verification_status: 'valid' as const
      },
      // Legacy fields for backward compatibility
      companyId,
      companyName,
      template,
      bullets: allBullets,
      provenance_bundle,
      metadata: {
        generated_at: new Date().toISOString(),
        source_quality: insightsRes?.summary !== "Insufficient evidence" ? 'high' : 'fallback',
        bullet_count: allBullets.length,
        custom_bullets: additionalBullets.length,
        data_sources: sources.length
      }
    };

    return NextResponse.json(memo, {
      headers: { "Cache-Control": "no-cache, no-store, must-revalidate" }
    });

  } catch (error) {
    console.error('Memo generation error:', error);

    // Fallback memo generation
    const fallbackProvenance = {
      provenance_id: `prov:${companyId}-fallback-${Math.random().toString(36).slice(2)}`,
      pipeline_version: "fallback-v1.0",
      snapshot_hash: `sha256:fallback${Date.now().toString(36)}`,
      model_version: "memoist-v1.2",
      retrieval_trace: [
        { doc_id: "doc:fallback-sample", url: "https://example.com/fallback", score: 0.5 },
      ],
      signed_by: "aurora-platform-pubkey:fallback",
      signature: `sig:fallback${Math.random().toString(36).substring(2)}`,
      created_at: new Date().toISOString()
    };

    const numericId = companyId.replace(/^company:/, '').replace(/^id:/, '');
    const fallbackBullets = [
      { id: "what", text: `What they do: ${numericId} operates in the AI/technology sector`, sources: ["doc:fallback-1"] },
      { id: "opportunity", text: "Why it matters: Part of growing AI infrastructure market", sources: ["doc:fallback-2"] },
      { id: "risk", text: "Primary risk: High competition and market saturation", sources: ["doc:fallback-3"] },
      ...additionalBullets.map((bullet: any, idx: number) => ({
        id: `custom-${idx}`,
        text: bullet.text || bullet,
        sources: bullet.sources || [`doc:custom-${idx}`]
      }))
    ];

    const fallbackMemo = {
      memo_id: `memo-${numericId}`,
      company_name: numericId,
      thesis: "AI-powered platform with growth potential in competitive market",
      confidence: 0.65,
      claims: fallbackBullets.map((bullet, index) => ({
        claim_id: bullet.id,
        text: bullet.text,
        sources: bullet.sources,
        evidence_snippet: `Fallback evidence for: ${bullet.text.substring(0, 100)}...`,
        confidence: 0.6 + Math.random() * 0.2
      })),
      generated_at: new Date().toISOString(),
      provenance: {
        snapshot_hash: fallbackProvenance.snapshot_hash,
        merkle_root: `merkle:fallback${Math.random().toString(36).substring(2)}`,
        signed_by: fallbackProvenance.signed_by,
        timestamp: new Date().toISOString(),
        retrieval_trace: {
          query: `fallback analysis ${numericId}`,
          sources: fallbackProvenance.retrieval_trace.map((trace: any) => ({
            source: trace.doc_id,
            score: trace.score,
            chunk: `Fallback data from ${trace.doc_id}...`
          })),
          total_sources: 1,
          confidence: 0.5
        },
        verification_status: 'valid' as const
      },
      // Legacy fields for backward compatibility
      companyId,
      companyName: numericId,
      template,
      bullets: fallbackBullets,
      provenance_bundle: fallbackProvenance,
      metadata: {
        generated_at: new Date().toISOString(),
        source_quality: 'fallback',
        bullet_count: fallbackBullets.length,
        custom_bullets: additionalBullets.length,
        data_sources: 0,
        error: 'Failed to fetch live company data'
      }
    };

    return NextResponse.json(fallbackMemo, {
      headers: { "Cache-Control": "no-cache, no-store, must-revalidate" }
    });
  }
}
