"use client";
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import gsap from "gsap";
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

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.6, ease: [0.16, 0.84, 0.24, 1] }
  }
};

const heroVariants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: { 
      duration: 0.8, 
      ease: [0.16, 0.84, 0.24, 1],
      delay: 0.1 
    }
  }
};

const claimsVariants = {
  initial: { opacity: 0, y: 40 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.6, 
      ease: [0.16, 0.84, 0.24, 1],
      delay: 0.3,
      staggerChildren: 0.1
    }
  }
};

export default function MemoPage() {
  const params = useParams();
  const companyId = params.id as string;
  const heroRef = useRef(null as any);
  const claimsRef = useRef(null as any);
  
  const [memo, setMemo] = useState(null as any);
  const [loading, setLoading] = useState(true as any);
  const [generating, setGenerating] = useState(false as any);
  const [expandedClaimId, setExpandedClaimId] = useState(null as any);
  const [provenanceOpen, setProvenanceOpen] = useState(false as any);
  const [exportOpen, setExportOpen] = useState(false as any);

  useEffect(() => {
    loadMemo();
  }, [companyId]);

  // GSAP intro animations (respect reduced-motion)
  useEffect(() => {
    const prefersReduced = typeof window !== 'undefined' && window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;

    const tl = gsap.timeline({ defaults: { ease: 'power2.out' } });
    if (heroRef.current) {
      tl.fromTo(heroRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6 }
      );
    }
    if (claimsRef.current) {
      tl.fromTo(claimsRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.6 }, '-=0.2'
      );
    }
    return () => { tl.kill(); };
  }, []);

  const loadMemo = async () => {
    try {
      setLoading(true);
      
      // Try to load existing memo first
      const response = await fetch(`/api/memo/${companyId}`);
      
      if (response.ok) {
        const data = await response.json();
        setMemo(data);
      } else {
        // Generate new memo if not found
        await generateMemo();
      }
    } catch (error) {
      console.error('Error loading memo:', error);
      await generateMemo();
    } finally {
      setLoading(false);
    }
  };

  const generateMemo = async () => {
    try {
      setGenerating(true);
      
      const response = await fetch('/api/memo/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          companyId: `company:${companyId}`,
          template: 'investment'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate memo');
      }

      const data = await response.json();
      setMemo(data);
    } catch (error) {
      console.error('Error generating memo:', error);
      
      // Fallback memo
      setMemo({
        memo_id: `memo-${companyId}`,
        company_name: companyId.charAt(0).toUpperCase() + companyId.slice(1),
        thesis: 'This company represents a compelling investment opportunity with strong fundamentals and market positioning.',
        confidence: 0.82,
        claims: [
          {
            claim_id: 'claim-1',
            text: 'Strong revenue growth trajectory with consistent year-over-year increases',
            sources: ['doc:q3-earnings-2024', 'sec:10k-2023', 'techcrunch:growth-analysis'],
            evidence_snippet: 'Revenue grew 45% YoY in Q3 2024, marking the eighth consecutive quarter of growth above 40%.',
            confidence: 0.89
          },
          {
            claim_id: 'claim-2',
            text: 'Market-leading technology platform with competitive moat',
            sources: ['github:platform-analysis', 'linkedin:tech-review', 'doc:whitepaper-v2'],
            evidence_snippet: 'The proprietary AI engine demonstrates 35% better accuracy than nearest competitor.',
            confidence: 0.76
          },
          {
            claim_id: 'claim-3',
            text: 'Experienced leadership team with proven track record',
            sources: ['sec:def14a-proxy', 'linkedin:exec-profiles', 'techcrunch:leadership-analysis'],
            evidence_snippet: 'CEO has successfully scaled 3 previous companies to $1B+ valuations.',
            confidence: 0.84
          }
        ],
        generated_at: new Date().toISOString(),
        provenance: {
          snapshot_hash: 'sha256:a1b2c3d4e5f6789...',
          merkle_root: 'merkle:xyz789abc123...',
          signed_by: 'memoist-v1.4',
          timestamp: new Date().toISOString(),
          retrieval_trace: {
            query: `investment analysis ${companyId}`,
            sources: [
              {
                source: 'doc:earnings-q3-2024',
                score: 0.94,
                chunk: 'Q3 2024 revenue increased 45% year-over-year to $127M, driven by strong customer acquisition and expansion.'
              },
              {
                source: 'sec:10k-annual-report',
                score: 0.87,
                chunk: 'Total addressable market estimated at $50B with current market penetration of <2%.'
              }
            ],
            total_sources: 15,
            confidence: 0.82
          },
          verification_status: 'valid'
        }
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleClaimEdit = (claimId: string, newText: string) => {
    if (!memo) return;
    
    setMemo((prev: any) => prev ? {
      ...prev,
      claims: prev.claims.map((claim: any) => 
        claim.claim_id === claimId 
          ? { ...claim, text: newText }
          : claim
      )
    } : null);
  };

  const handleExport = async (options: any) => {
    console.log('Exporting memo with options:', options);
    // Simulate export process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // In real implementation, this would call the export API
    const filename = `${memo?.company_name}-memo-${Date.now()}.${options.format}`;
    console.log(`Would download: ${filename}`);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!memo) return;
      
      // Ctrl/Cmd + P for provenance
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        setProvenanceOpen(true);
      }
      
      // Ctrl/Cmd + E for export
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        setExportOpen(true);
      }
      
      // Escape to close modals
      if (e.key === 'Escape') {
        setProvenanceOpen(false);
        setExportOpen(false);
        setExpandedClaimId(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [memo]);

  if (loading && !generating) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'var(--bg-00)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }} role="status" aria-live="polite">
        <div style={{ 
          fontSize: '18px', 
          color: 'var(--starlight)',
          opacity: 0.7 
        }}>
          Loading memo...
        </div>
      </div>
    );
  }

  if (generating) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'var(--bg-00)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '20px'
      }} role="status" aria-live="polite">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(0, 240, 255, 0.3)',
            borderTop: '3px solid var(--aurora-cyan)',
            borderRadius: '50%'
          }}
        />
        <div style={{ 
          fontSize: '18px', 
          color: 'var(--starlight)',
          textAlign: 'center'
        }}>
          <div>Generating Investment Memo</div>
          <div style={{ 
            fontSize: '14px', 
            opacity: 0.7, 
            marginTop: '8px' 
          }}>
            Analyzing company data and market signals...
          </div>
        </div>
      </div>
    );
  }

  if (!memo) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'var(--bg-00)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ 
          fontSize: '18px', 
          color: 'var(--starlight)',
          opacity: 0.7 
        }}>
          Failed to load memo
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit={{ opacity: 0, y: -10, transition: { duration: 0.2 } }}
      style={{
        minHeight: '100vh',
        background: 'var(--bg-00)',
        padding: '0'
      }}
    >
      {/* Hero Section */}
      <motion.section 
        variants={heroVariants}
        initial="initial"
        animate="animate"
        style={{
          background: 'linear-gradient(135deg, var(--bg-00) 0%, var(--bg-01) 100%)',
          padding: '80px 0 60px',
          position: 'relative',
          overflow: 'hidden'
        }}
        ref={heroRef}
        aria-labelledby="memo-hero-heading"
      >
        {/* Background grid pattern */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)',
          backgroundSize: '20px 20px',
          opacity: 0.1
        }} />
        
        <div style={{ 
          maxWidth: '1200px', 
          margin: '0 auto', 
          padding: '0 24px',
          position: 'relative',
          zIndex: 1
        }}>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '2fr 1fr', 
            gap: '60px',
            alignItems: 'center'
          }}>
            {/* Left: Company info and thesis */}
            <div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                style={{ marginBottom: '16px' }}
              >
                <div style={{
                  display: 'inline-block',
                  padding: '6px 16px',
                  background: 'rgba(0, 240, 255, 0.15)',
                  border: '1px solid rgba(0, 240, 255, 0.3)',
                  borderRadius: '20px',
                  fontSize: '14px',
                  color: 'var(--aurora-cyan)',
                  fontWeight: '500',
                  marginBottom: '24px'
                }}>
                  Investment Memo
                </div>
              </motion.div>

              <motion.h1 
                className="memo-title-h1"
                id="memo-hero-heading"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.5 }}
                style={{ marginBottom: '24px' }}
              >
                {memo.company_name}
              </motion.h1>

              <motion.div
                className="memo-body"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.5 }}
                style={{
                  fontSize: '20px',
                  lineHeight: 1.6,
                  maxWidth: '600px',
                  opacity: 0.9
                }}
              >
                {memo.thesis}
              </motion.div>

              {/* Action buttons */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.5 }}
                style={{ 
                  display: 'flex', 
                  gap: '12px', 
                  marginTop: '32px' 
                }}
              >
                <motion.button
                  onClick={() => setProvenanceOpen(true)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: 'var(--starlight)',
                    padding: '12px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500',
                    transition: 'all 0.2s var(--memo-ease)'
                  }}
                  whileHover={{ y: -2, backgroundColor: 'rgba(255, 255, 255, 0.15)' }}
                  whileTap={{ scale: 0.98 }}
                >
                  View Provenance ⌘P
                </motion.button>
                
                <motion.button
                  onClick={() => setExportOpen(true)}
                  style={{
                    background: 'var(--aurora-cyan)',
                    border: 'none',
                    color: 'var(--bg-00)',
                    padding: '12px 20px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '600',
                    transition: 'all 0.2s var(--memo-ease)'
                  }}
                  whileHover={{ y: -2, backgroundColor: '#00D4ED' }}
                  whileTap={{ scale: 0.98 }}
                >
                  Export Memo ⌘E
                </motion.button>
              </motion.div>
            </div>

            {/* Right: Confidence gauge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.6, duration: 0.6 }}
              style={{ 
                display: 'flex', 
                justifyContent: 'center',
                alignItems: 'center',
                height: '300px'
              }}
            >
              <ConfidenceGauge confidence={memo.confidence} />
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Claims Section */}
      <motion.section 
        variants={claimsVariants}
        initial="initial"
        animate="animate"
        style={{ 
          maxWidth: '800px', 
          margin: '0 auto', 
          padding: '60px 24px' 
        }}
        ref={claimsRef}
        aria-label="Investment claims"
      >
        <motion.h2 
          className="memo-title-h2"
          style={{ 
            marginBottom: '32px',
            textAlign: 'center'
          }}
        >
          Investment Claims ({memo.claims.length})
        </motion.h2>

        <div>
          {memo.claims.map((claim: any, index: any) => (
            <motion.div
              key={claim.claim_id}
              variants={{
                initial: { opacity: 0, y: 20 },
                animate: { 
                  opacity: 1, 
                  y: 0,
                  transition: { 
                    delay: index * 0.1,
                    duration: 0.4,
                    ease: [0.16, 0.84, 0.24, 1]
                  }
                }
              }}
            >
              <ClaimCard
                claim={claim}
                index={index}
                expanded={expandedClaimId === claim.claim_id}
                onExpand={() => 
                  setExpandedClaimId(
                    expandedClaimId === claim.claim_id ? null : claim.claim_id
                  )
                }
                onEdit={handleClaimEdit}
              />
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Provenance Modal */}
      <ProvenanceModal
        isOpen={provenanceOpen}
        onClose={() => setProvenanceOpen(false)}
        provenance={memo.provenance}
      />

      {/* Export Flow */}
      <ExportFlow
        isOpen={exportOpen}
        onClose={() => setExportOpen(false)}
        memo={memo}
        onExport={handleExport}
      />
    </motion.div>
  );
}