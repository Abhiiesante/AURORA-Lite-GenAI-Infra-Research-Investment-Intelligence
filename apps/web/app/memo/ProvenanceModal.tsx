"use client";
import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface ProvenanceData {
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
}

interface ProvenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  provenance: ProvenanceData;
}

const modalVariants = {
  hidden: { 
    opacity: 0, 
    scale: 0.95,
    y: 20 
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: { 
      duration: 0.3, 
      ease: [0.16, 0.84, 0.24, 1] 
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    y: 20,
    transition: { 
      duration: 0.2, 
      ease: [0.16, 0.84, 0.24, 1] 
    }
  }
};

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { duration: 0.2 }
  },
  exit: { 
    opacity: 0,
    transition: { duration: 0.2 }
  }
};

const tabVariants = {
  inactive: { 
    color: 'rgba(230, 238, 252, 0.6)',
    borderBottomColor: 'transparent'
  },
  active: { 
    color: 'var(--aurora-cyan)',
    borderBottomColor: 'var(--aurora-cyan)'
  }
};

export function ProvenanceModal({ isOpen, onClose, provenance }: ProvenanceModalProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [copied, setCopied] = useState(null as any);
  const dialogRef = useRef(null as any);
  const lastFocusedRef = useRef(null as any);

  const copyToClipboard = async (text: string, label: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  const formatHash = (hash: string) => {
    return `${hash.slice(0, 8)}...${hash.slice(-8)}`;
  };

  const getVerificationStatusColor = (status: string) => {
    switch (status) {
      case 'valid': return '#51CF66';
      case 'invalid': return '#FF6B6B';
      case 'pending': return '#FFB86B';
      default: return 'var(--starlight)';
    }
  };

  const getVerificationIcon = (status: string) => {
    switch (status) {
      case 'valid': return '✓';
      case 'invalid': return '✗';
      case 'pending': return '⏳';
      default: return '?';
    }
  };

  // Focus trap and restore
  useEffect(() => {
    if (!isOpen) return;
    lastFocusedRef.current = document.activeElement as any;
    const el = dialogRef.current as HTMLElement | null;
    if (el) {
      const heading = el.querySelector('#provenance-heading') as any;
      if (heading && (heading as any).focus) {
        (heading as any).setAttribute('tabindex', '-1');
        (heading as any).focus();
      }
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const el = dialogRef.current as HTMLElement | null;
      if (!el) return;
      const focusables = Array.from(
        el.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
      ) as HTMLElement[];
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (e.shiftKey) {
        if (active === first || !el.contains(active)) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (active === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      const prev = lastFocusedRef.current as any;
      if (prev && prev.focus) prev.focus();
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="provenance-modal-backdrop"
          variants={backdropVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(5, 7, 10, 0.8)',
            backdropFilter: 'blur(8px)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="provenance-heading"
          onKeyDown={(e: any) => { if (e.key === 'Escape') onClose(); }}
          onClick={onClose}
        >
          <motion.div
            className="provenance-modal memo-glass"
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            style={{
              width: '90vw',
              maxWidth: '800px',
              maxHeight: '90vh',
              background: 'var(--memo-bg)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}
            onClick={(e: any) => e.stopPropagation()}
            ref={dialogRef}
          >
            {/* Header */}
            <div style={{
              padding: '24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <h2 id="provenance-heading" className="memo-title-h2" style={{ marginBottom: '4px' }}>
                  Provenance & Verification
                </h2>
                <p className="memo-body" style={{ 
                  opacity: 0.7, 
                  fontSize: '14px',
                  margin: 0
                }}>
                  Cryptographic audit trail for this memo
                </p>
              </div>
              <button
                onClick={onClose}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'rgba(230, 238, 252, 0.6)',
                  fontSize: '24px',
                  cursor: 'pointer',
                  padding: '8px'
                }}
              >
                ×
              </button>
            </div>

            {/* Tabs */}
            <div style={{
              display: 'flex',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '0 24px'
            }}>
              {[
                { key: 'overview', label: 'Overview' },
                { key: 'verification', label: 'Verification' },
                { key: 'trace', label: 'Retrieval Trace' },
                { key: 'raw', label: 'Raw Data' }
              ].map((tab) => (
                <motion.button
                  key={tab.key}
                  variants={tabVariants}
                  animate={activeTab === tab.key ? 'active' : 'inactive'}
                  onClick={() => setActiveTab(tab.key as any)}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: '12px 16px',
                    fontSize: '14px',
                    cursor: 'pointer',
                    borderBottom: '2px solid',
                    transition: 'all 0.2s var(--micro-ease)'
                  }}
                >
                  {tab.label}
                </motion.button>
              ))}
            </div>

            {/* Content */}
            <div style={{
              flex: 1,
              padding: '24px',
              overflow: 'auto'
            }}>
              {activeTab === 'overview' && (
                <div>
                  {/* Verification status */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '16px',
                    background: `${getVerificationStatusColor(provenance.verification_status)}15`,
                    border: `1px solid ${getVerificationStatusColor(provenance.verification_status)}30`,
                    borderRadius: '8px',
                    marginBottom: '24px'
                  }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: getVerificationStatusColor(provenance.verification_status),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--bg-00)',
                      fontSize: '16px',
                      fontWeight: 'bold'
                    }}>
                      {getVerificationIcon(provenance.verification_status)}
                    </div>
                    <div>
                      <div style={{
                        fontSize: '16px',
                        fontWeight: '600',
                        color: getVerificationStatusColor(provenance.verification_status),
                        textTransform: 'capitalize'
                      }}>
                        {provenance.verification_status}
                      </div>
                      <div className="memo-body" style={{ fontSize: '14px', opacity: 0.8 }}>
                        {provenance.verification_status === 'valid' 
                          ? 'All signatures and hashes verified'
                          : provenance.verification_status === 'invalid'
                          ? 'Verification failed - data may be compromised'
                          : 'Verification in progress...'
                        }
                      </div>
                    </div>
                  </div>

                  {/* Key metrics */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '16px',
                    marginBottom: '24px'
                  }}>
                    <div className="memo-page" style={{ padding: '16px' }}>
                      <div className="memo-label" style={{ marginBottom: '8px' }}>
                        Snapshot Hash
                      </div>
                      <code 
                        style={{ 
                          fontSize: '12px', 
                          color: 'var(--aurora-cyan)',
                          cursor: 'pointer'
                        }}
                        onClick={() => copyToClipboard(provenance.snapshot_hash, 'hash')}
                      >
                        {formatHash(provenance.snapshot_hash)}
                        {copied === 'hash' && ' ✓'}
                      </code>
                    </div>
                    
                    <div className="memo-page" style={{ padding: '16px' }}>
                      <div className="memo-label" style={{ marginBottom: '8px' }}>
                        Signed By
                      </div>
                      <div className="memo-body" style={{ fontSize: '14px' }}>
                        {provenance.signed_by}
                      </div>
                    </div>

                    <div className="memo-page" style={{ padding: '16px' }}>
                      <div className="memo-label" style={{ marginBottom: '8px' }}>
                        Generated
                      </div>
                      <div className="memo-body" style={{ fontSize: '14px' }}>
                        {new Date(provenance.timestamp).toLocaleString()}
                      </div>
                    </div>

                    <div className="memo-page" style={{ padding: '16px' }}>
                      <div className="memo-label" style={{ marginBottom: '8px' }}>
                        Confidence
                      </div>
                      <div style={{
                        fontSize: '18px',
                        fontWeight: '600',
                        color: provenance.retrieval_trace.confidence > 0.8 ? '#51CF66' : 
                               provenance.retrieval_trace.confidence > 0.6 ? '#FFB86B' : '#FF6B6B'
                      }}>
                        {Math.round(provenance.retrieval_trace.confidence * 100)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'verification' && (
                <div>
                  <div className="memo-page" style={{ padding: '20px', marginBottom: '16px' }}>
                    <h3 style={{ marginBottom: '16px', color: 'var(--starlight)' }}>
                      Cryptographic Verification
                    </h3>
                    
                    {/* Merkle root */}
                    <div style={{ marginBottom: '16px' }}>
                      <div className="memo-label" style={{ marginBottom: '8px' }}>
                        Merkle Root
                      </div>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        borderRadius: '4px'
                      }}>
                        <code style={{ 
                          fontSize: '12px', 
                          color: 'var(--aurora-cyan)',
                          flex: 1
                        }}>
                          {provenance.merkle_root}
                        </code>
                        <button
                          onClick={() => copyToClipboard(provenance.merkle_root, 'merkle')}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'rgba(230, 238, 252, 0.6)',
                            cursor: 'pointer'
                          }}
                        >
                          {copied === 'merkle' ? '✓' : '📋'}
                        </button>
                      </div>
                    </div>

                    {/* Full snapshot hash */}
                    <div style={{ marginBottom: '16px' }}>
                      <div className="memo-label" style={{ marginBottom: '8px' }}>
                        Full Snapshot Hash
                      </div>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px',
                        background: 'rgba(255, 255, 255, 0.05)',
                        borderRadius: '4px'
                      }}>
                        <code style={{ 
                          fontSize: '12px', 
                          color: 'var(--aurora-cyan)',
                          flex: 1,
                          wordBreak: 'break-all'
                        }}>
                          {provenance.snapshot_hash}
                        </code>
                        <button
                          onClick={() => copyToClipboard(provenance.snapshot_hash, 'full-hash')}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'rgba(230, 238, 252, 0.6)',
                            cursor: 'pointer'
                          }}
                        >
                          {copied === 'full-hash' ? '✓' : '📋'}
                        </button>
                      </div>
                    </div>

                    {/* Signature verification */}
                    <div>
                      <div className="memo-label" style={{ marginBottom: '8px' }}>
                        Digital Signature
                      </div>
                      <div style={{
                        padding: '12px',
                        background: provenance.verification_status === 'valid' 
                          ? 'rgba(81, 207, 102, 0.1)' 
                          : 'rgba(255, 107, 107, 0.1)',
                        border: `1px solid ${provenance.verification_status === 'valid' ? '#51CF66' : '#FF6B6B'}30`,
                        borderRadius: '6px'
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          marginBottom: '8px'
                        }}>
                          <div style={{
                            color: provenance.verification_status === 'valid' ? '#51CF66' : '#FF6B6B'
                          }}>
                            {getVerificationIcon(provenance.verification_status)}
                          </div>
                          <span className="memo-body" style={{ fontSize: '14px' }}>
                            Signature {provenance.verification_status}
                          </span>
                        </div>
                        <div className="memo-body" style={{ fontSize: '12px', opacity: 0.8 }}>
                          Signed by: {provenance.signed_by}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'trace' && (
                <div>
                  <div className="memo-page" style={{ padding: '20px', marginBottom: '16px' }}>
                    <h3 style={{ marginBottom: '8px', color: 'var(--starlight)' }}>
                      Retrieval Query
                    </h3>
                    <code style={{
                      display: 'block',
                      padding: '12px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: '6px',
                      fontSize: '14px',
                      color: 'var(--aurora-cyan)'
                    }}>
                      {provenance.retrieval_trace.query}
                    </code>
                  </div>

                  <div className="memo-page" style={{ padding: '20px' }}>
                    <h3 style={{ marginBottom: '16px', color: 'var(--starlight)' }}>
                      Retrieved Sources ({provenance.retrieval_trace.total_sources})
                    </h3>
                    
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      {provenance.retrieval_trace.sources.map((source, index) => (
                        <div
                          key={index}
                          style={{
                            padding: '12px',
                            marginBottom: '12px',
                            background: 'rgba(255, 255, 255, 0.03)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '6px'
                          }}
                        >
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '8px'
                          }}>
                            <code style={{
                              fontSize: '12px',
                              color: 'var(--aurora-cyan)'
                            }}>
                              {source.source}
                            </code>
                            <div style={{
                              padding: '2px 6px',
                              background: source.score > 0.8 ? '#51CF6630' : 
                                        source.score > 0.6 ? '#FFB86B30' : '#FF6B6B30',
                              color: source.score > 0.8 ? '#51CF66' : 
                                    source.score > 0.6 ? '#FFB86B' : '#FF6B6B',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontFamily: 'Space Grotesk, monospace'
                            }}>
                              {Math.round(source.score * 100)}%
                            </div>
                          </div>
                          <div className="memo-body" style={{
                            fontSize: '13px',
                            opacity: 0.8,
                            lineHeight: 1.4
                          }}>
                            {source.chunk.length > 200 
                              ? `${source.chunk.substring(0, 200)}...`
                              : source.chunk
                            }
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'raw' && (
                <div className="memo-page" style={{ padding: '20px' }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '16px'
                  }}>
                    <h3 style={{ color: 'var(--starlight)' }}>
                      Raw Provenance Data
                    </h3>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(provenance, null, 2), 'raw')}
                      style={{
                        background: 'var(--aurora-cyan)',
                        color: 'var(--bg-00)',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      {copied === 'raw' ? 'Copied!' : 'Copy JSON'}
                    </button>
                  </div>
                  
                  <pre style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '16px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    color: 'var(--starlight)',
                    overflow: 'auto',
                    maxHeight: '400px',
                    lineHeight: 1.4
                  }}>
                    {JSON.stringify(provenance, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* Footer */}
            <div style={{
              padding: '16px 24px',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '8px'
            }}>
              <button
                onClick={onClose}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: 'var(--starlight)',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}