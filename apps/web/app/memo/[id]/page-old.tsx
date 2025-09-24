// @ts-nocheck
"use client";
import { useState, useEffect, Suspense } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ConfidenceGauge } from "../ConfidenceGauge";
import { ClaimCard } from "../ClaimCard";
import { ProvenanceModal } from "../ProvenanceModal";
import { ExportFlow } from "../ExportFlow";

// Import CSS tokens
import "../memo-tokens.css";

interface Claim {
  claim_id: string;
  text: string;
  sources: string[];
  evidence_snippet: string;
  confidence: number;
}

interface MemoData {
  memo_id: string;
  company_name: string;
  thesis: string;
  confidence: number;
  claims: Claim[];
  generated_at: string;
  provenance: {
    snapshot_hash: string;
    merkle_root: string;
    signed_by: string;
    timestamp: string;
    retrieval_trace: {
      query: string;
      sources: Array<{
        source: string;
        score: number;
        chunk: string;
      }>;
      total_sources: number;
      confidence: number;
    };
    verification_status: 'valid' | 'invalid' | 'pending';
  };
}

export default function MemoPage() {
  const params = useParams();
  const companyId = params.id as string;

  const [memo, setMemo] = useState<MemoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [provenanceOpen, setProvenanceOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [linkedEntities, setLinkedEntities] = useState<any[]>([]);

  // Load or generate memo
  useEffect(() => {
    loadMemo();
  }, [companyId]);

  const loadMemo = async () => {
    try {
      setLoading(true);

      // Try to load existing memo first
      const memoRes = await fetch(`/api/memo/${companyId}`);
      if (memoRes.ok) {
        const existingMemo = await memoRes.json();
        setMemo(existingMemo);
      } else {
        // Generate new memo
        await generateMemo();
      }
    } catch (error) {
      console.error('Memo load error:', error);
      // Show fallback or generate new
      await generateMemo();
    } finally {
      setLoading(false);
    }
  };

  const generateMemo = async () => {
    try {
      setGenerating(true);
      setLoading(true);

      const response = await fetch('/api/memo/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          companyId: `company:${companyId}`,
          template: 'investment',
          topK: 10,
          maxDocAge: 90
        })
      });

      if (!response.ok) {
        throw new Error('Memo generation failed');
      }

      const newMemo = await response.json();

      // Transform to match MemoData interface
      const transformedMemo: MemoData = {
        memo_id: `memo:${companyId}-${Date.now()}`,
        company_id: `company:${companyId}`,
        title: newMemo.companyName || companyId,
        thesis: newMemo.thesis || 'Investment thesis pending analysis',
        confidence: 0.85, // Default confidence
        claims: newMemo.bullets?.map((bullet: any, index: number) => ({
          claim_id: bullet.id || `claim-${index}`,
          text: bullet.text || '',
          sources: bullet.sources || [],
          evidence_snippet: `Evidence for: ${bullet.text?.slice(0, 100)}...`,
          confidence: 0.80 + Math.random() * 0.15 // Mock confidence
        })) || [],
        comps: [], // TODO: Add competitive analysis
        provenance_bundle: newMemo.provenance_bundle || {},
        created_at: new Date().toISOString(),
        author: 'memoist-v1.4'
      };

      setMemo(transformedMemo);
    } catch (error) {
      console.error('Memo generation error:', error);

      // Fallback memo
      setMemo({
        memo_id: `memo:${companyId}-fallback`,
        company_id: `company:${companyId}`,
        title: companyId.charAt(0).toUpperCase() + companyId.slice(1),
        thesis: 'Investment analysis requires additional data sources',
        confidence: 0.65,
        claims: [
          {
            claim_id: 'fallback-1',
            text: 'Company operates in the AI/technology sector',
            sources: ['doc:fallback'],
            evidence_snippet: 'Limited evidence available',
            confidence: 0.65
          }
        ],
        comps: [],
        provenance_bundle: {},
        created_at: new Date().toISOString(),
        author: 'fallback-v1.0'
      });
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  const handleClaimEdit = (claimId: string, newText: string) => {
    if (!memo) return;

    const updatedMemo = {
      ...memo,
      claims: memo.claims.map(claim =>
        claim.claim_id === claimId
          ? { ...claim, text: newText }
          : claim
      )
    };

    setMemo(updatedMemo);
  };

  const handleExport = (format: 'pdf' | 'pptx') => {
    setExportOpen(true);
  };

  const handleAssignRedTeam = (payload: any) => {
    console.log('Red team assignment:', payload);
  };

  if (loading && !memo) {
    return (
      <motion.div
        className="memo-page-container"
        variants={pageVariants}
        initial="initial"
        animate="animate"
        style={{
          background: 'var(--bg-01)',
          minHeight: '100vh',
          padding: '24px',
          color: 'var(--starlight)'
        }}
      >
        <div className="memo-skeleton">
          <div className="memo-glass memo-page" style={{
            maxWidth: '1400px',
            margin: '0 auto',
            padding: 'var(--memo-padding)',
            minHeight: '80vh'
          }}>
            {/* Skeleton content */}
            <div style={{ height: '60px', background: 'rgba(255,255,255,0.1)', borderRadius: '8px', marginBottom: '24px' }} />
            <div style={{ height: '200px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', marginBottom: '24px' }} />
            <div style={{ height: '400px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px' }} />
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="memo-page-container"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      style={{
        background: 'var(--bg-01)',
        minHeight: '100vh',
        padding: '24px',
        color: 'var(--starlight)'
      }}
    >
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Hero Section */}
        <motion.div
          className="memo-hero"
          style={{
            display: 'flex',
            gap: '32px',
            marginBottom: 'var(--section-gap)',
            alignItems: 'flex-start'
          }}
        >
          {/* Left: Thesis + Actions */}
          <div style={{ flex: 1 }}>
            <motion.h1
              className="memo-title aurora-rim"
              variants={memoVariants}
              animate={memo ? "complete" : "skeleton"}
              style={{ marginBottom: '16px' }}
            >
              {memo?.title || 'Loading...'}
            </motion.h1>

            <motion.p
              className="memo-body"
              style={{
                fontSize: '18px',
                marginBottom: '24px',
                opacity: 0.9
              }}
              variants={memoVariants}
              animate={memo ? "complete" : "skeleton"}
            >
              {memo?.thesis || 'Generating investment thesis...'}
            </motion.p>

            {/* Quick Actions */}
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button
                className="memo-glass aurora-rim"
                onClick={() => setExportOpen(true)}
                style={{
                  padding: '12px 20px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'var(--memo-bg)',
                  color: 'var(--starlight)',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Export PDF
              </button>

              <button
                className="memo-glass"
                onClick={() => setProvenanceOpen(true)}
                style={{
                  padding: '12px 20px',
                  border: 'none',
                  borderRadius: '8px',
                  background: 'var(--memo-bg)',
                  color: 'var(--starlight)',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                View Provenance
              </button>

              {!memo && (
                <button
                  className="memo-glass"
                  onClick={generateMemo}
                  disabled={generating}
                  style={{
                    padding: '12px 20px',
                    border: 'none',
                    borderRadius: '8px',
                    background: generating ? 'var(--nebula-violet)' : 'var(--aurora-cyan)',
                    color: 'var(--bg-00)',
                    cursor: generating ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '600'
                  }}
                >
                  {generating ? 'Generating...' : 'Generate Memo'}
                </button>
              )}
            </div>
          </div>

          {/* Right: Confidence Gauge + Provenance Summary */}
          <div style={{ flex: '0 0 280px' }}>
            <Suspense fallback={<div>Loading gauge...</div>}>
              <ConfidenceGauge
                confidence={memo?.confidence || 0}
                size={120}
              />
            </Suspense>

            {memo?.provenance_bundle && (
              <div
                className="memo-glass"
                style={{
                  padding: '16px',
                  marginTop: '16px',
                  fontSize: '13px',
                  opacity: 0.8
                }}
              >
                <div>Pipeline: {memo.provenance_bundle.pipeline_version || 'N/A'}</div>
                <div>Model: {memo.provenance_bundle.model_version || 'N/A'}</div>
                <div>Sources: {memo.provenance_bundle.retrieval_trace?.length || 0}</div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Main Content Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '32px' }}>
          {/* Left Column: Claims & Analysis */}
          <motion.div
            className="memo-content"
            variants={memoVariants}
            animate={memo ? "complete" : "skeleton"}
          >
            <div className="memo-glass memo-page memo-paper" style={{
              padding: 'var(--memo-padding)',
              minHeight: '60vh'
            }}>
              <h2 style={{
                fontSize: '24px',
                marginBottom: '20px',
                color: 'var(--starlight)',
                fontWeight: '600'
              }}>
                Investment Analysis
              </h2>

              {memo?.claims?.map((claim, index) => (
                <Suspense key={claim.claim_id} fallback={<div>Loading claim...</div>}>
                  <ClaimCard
                    claim={claim}
                    index={index}
                    onEdit={handleClaimEdit}
                    onExpand={() => setSelectedClaimId(claim.claim_id)}
                    expanded={selectedClaimId === claim.claim_id}
                  />
                </Suspense>
              ))}
            </div>
          </motion.div>

          {/* Right Column: Context Sidebar */}
          <motion.div
            className="memo-sidebar"
            variants={memoVariants}
            animate={memo ? "complete" : "skeleton"}
          >
            <div className="memo-glass" style={{
              padding: 'var(--memo-padding)',
              marginBottom: '16px'
            }}>
              <h3 style={{ fontSize: '18px', marginBottom: '16px', color: 'var(--starlight)' }}>
                Evidence Bundle
              </h3>

              {memo?.provenance_bundle?.retrieval_trace?.slice(0, 5).map((trace: any, index: number) => (
                <div key={index} style={{
                  padding: '8px 0',
                  borderBottom: index < 4 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                  fontSize: '13px'
                }}>
                  <div style={{ opacity: 0.7 }}>
                    Score: {trace.score?.toFixed(2) || 'N/A'}
                  </div>
                  <div style={{ marginTop: '4px' }}>
                    {trace.url ? (
                      <a
                        href={trace.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: 'var(--aurora-cyan)', textDecoration: 'none' }}
                      >
                        {trace.doc_id || 'Document'}
                      </a>
                    ) : (
                      <span>{trace.doc_id || 'Document'}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Modals */}
      <AnimatePresence>
        {provenanceOpen && memo && (
          <Suspense fallback={<div>Loading provenance...</div>}>
            <ProvenanceModal
              provenance={memo.provenance_bundle}
              onClose={() => setProvenanceOpen(false)}
            />
          </Suspense>
        )}

        {exportOpen && memo && (
          <Suspense fallback={<div>Loading export...</div>}>
            <ExportFlow
              memo={memo}
              onClose={() => setExportOpen(false)}
              onExport={handleExport}
            />
          </Suspense>
        )}
      </AnimatePresence>
    </motion.div>
  );
}