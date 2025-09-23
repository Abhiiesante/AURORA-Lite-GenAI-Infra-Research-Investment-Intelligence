"use client";
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Claim {
  claim_id: string;
  text: string;
  sources: string[];
  evidence_snippet: string;
  confidence: number;
}

interface ClaimCardProps {
  claim: Claim;
  index: number;
  onEdit: (claimId: string, newText: string) => void;
  onExpand: () => void;
  expanded: boolean;
}

const claimVariants = {
  rest: { 
    y: 0, 
    rotateX: 0, 
    boxShadow: "0 4px 16px rgba(0, 0, 0, 0.25)" 
  },
  hover: { 
    y: -2, 
    rotateX: 0.5,
    boxShadow: "0 8px 24px rgba(0, 0, 0, 0.35)",
    transition: { duration: 0.14, ease: [0.2, 0.9, 0.3, 1] } 
  },
  expanded: {
    scale: 1.02,
    boxShadow: "0 12px 32px rgba(0, 0, 0, 0.4)",
    transition: { duration: 0.36, ease: [0.16, 0.84, 0.24, 1] }
  }
};

const evidenceVariants = {
  collapsed: { 
    height: 0, 
    opacity: 0,
    transition: { duration: 0.3, ease: [0.16, 0.84, 0.24, 1] }
  },
  expanded: { 
    height: "auto", 
    opacity: 1,
    transition: { duration: 0.4, ease: [0.16, 0.84, 0.24, 1] }
  }
};

const sourceChipVariants = {
  initial: { scale: 0, opacity: 0 },
  animate: { 
    scale: 1, 
    opacity: 1,
    transition: { duration: 0.2, ease: [0.2, 0.9, 0.3, 1] }
  },
  hover: {
    scale: 1.05,
    backgroundColor: "var(--aurora-cyan)",
    color: "var(--bg-00)",
    transition: { duration: 0.15 }
  }
};

export function ClaimCard({ claim, index, onEdit, onExpand, expanded }: ClaimCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(claim.text);

  const handleSave = () => {
    onEdit(claim.claim_id, editText);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditText(claim.text);
    setIsEditing(false);
  };

  // Get confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence < 0.6) return '#FF6B6B';
    if (confidence < 0.8) return '#FFB86B';
    return '#51CF66';
  };

  // Extract domain from source
  const getDomainFromSource = (source: string) => {
    if (source.includes('sec.gov')) return 'SEC';
    if (source.includes('techcrunch')) return 'TechCrunch';
    if (source.includes('github')) return 'GitHub';
    if (source.includes('linkedin')) return 'LinkedIn';
    return source.replace('doc:', '').split('-')[0].toUpperCase();
  };

  return (
    <motion.div
      className="claim-card memo-glass memo-page"
      variants={claimVariants}
      initial="rest"
      whileHover="hover"
      animate={expanded ? "expanded" : "rest"}
      style={{
        padding: 'var(--claim-padding)',
        marginBottom: '16px',
        cursor: 'pointer',
        position: 'relative',
        background: expanded 
          ? 'rgba(255, 255, 255, 0.04)' 
          : 'var(--memo-bg)'
      }}
      onClick={onExpand}
    >
      {/* Claim header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'flex-start',
        marginBottom: '12px'
      }}>
        <div style={{ flex: 1, marginRight: '16px' }}>
          {/* Claim number */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            background: 'var(--aurora-cyan)',
            color: 'var(--bg-00)',
            fontSize: '12px',
            fontWeight: '600',
            marginBottom: '8px',
            fontFamily: 'Space Grotesk, monospace'
          }}>
            {index + 1}
          </div>

          {/* Claim text */}
          {isEditing ? (
            <div onClick={(e: any) => e.stopPropagation()}>
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                style={{
                  width: '100%',
                  minHeight: '60px',
                  padding: '8px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid var(--aurora-cyan)',
                  borderRadius: '4px',
                  color: 'var(--starlight)',
                  fontSize: 'var(--claim-size)',
                  fontFamily: 'inherit',
                  resize: 'vertical'
                }}
                autoFocus
              />
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button
                  onClick={handleSave}
                  style={{
                    padding: '4px 12px',
                    background: 'var(--aurora-cyan)',
                    color: 'var(--bg-00)',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  Save
                </button>
                <button
                  onClick={handleCancel}
                  style={{
                    padding: '4px 12px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: 'var(--starlight)',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div 
              className="memo-body"
              style={{ 
                fontSize: 'var(--claim-size)',
                lineHeight: 1.5,
                marginBottom: '12px'
              }}
            >
              {claim.text}
            </div>
          )}

          {/* Source chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {claim.sources.map((source, sourceIndex) => (
              <motion.span
                key={sourceIndex}
                variants={sourceChipVariants}
                initial="initial"
                animate="animate"
                whileHover="hover"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '4px 8px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: '500',
                  color: 'var(--starlight)',
                  cursor: 'pointer',
                  transition: 'all 0.15s var(--micro-ease)'
                }}
                onClick={(e: any) => {
                  e.stopPropagation();
                  console.log('Source clicked:', source);
                }}
              >
                {getDomainFromSource(source)}
              </motion.span>
            ))}
          </div>
        </div>

        {/* Confidence indicator + Actions */}
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'flex-end',
          gap: '8px'
        }}>
          {/* Confidence badge */}
          <div
            style={{
              padding: '4px 8px',
              borderRadius: '12px',
              background: `${getConfidenceColor(claim.confidence)}20`,
              border: `1px solid ${getConfidenceColor(claim.confidence)}40`,
              fontSize: '11px',
              fontWeight: '500',
              color: getConfidenceColor(claim.confidence),
              fontFamily: 'Space Grotesk, monospace'
            }}
          >
            {Math.round(claim.confidence * 100)}%
          </div>

          {/* Edit button */}
          {!isEditing && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'rgba(230, 238, 252, 0.6)',
                fontSize: '12px',
                cursor: 'pointer',
                padding: '4px'
              }}
              title="Edit claim"
            >
              ✎
            </button>
          )}
        </div>
      </div>

      {/* Expandable evidence section */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            variants={evidenceVariants}
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            style={{ overflow: 'hidden' }}
            onClick={(e: any) => e.stopPropagation()}
          >
            <div style={{
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              paddingTop: '16px',
              marginTop: '16px'
            }}>
              <h4 style={{
                fontSize: '14px',
                fontWeight: '600',
                color: 'var(--starlight)',
                marginBottom: '8px'
              }}>
                Supporting Evidence
              </h4>
              
              <div 
                className="memo-body"
                style={{
                  fontSize: '14px',
                  opacity: 0.8,
                  background: 'rgba(255, 255, 255, 0.05)',
                  padding: '12px',
                  borderRadius: '6px',
                  borderLeft: '3px solid var(--aurora-cyan)'
                }}
              >
                {claim.evidence_snippet}
              </div>

              {/* Evidence actions */}
              <div style={{ 
                display: 'flex', 
                gap: '8px', 
                marginTop: '12px',
                fontSize: '12px'
              }}>
                <button
                  style={{
                    background: 'none',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: 'var(--starlight)',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  View Sources
                </button>
                <button
                  style={{
                    background: 'none',
                    border: '1px solid rgba(255, 184, 107, 0.3)',
                    color: 'var(--solar-amber)',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Flag for Review
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Expand/collapse indicator */}
      <motion.div
        style={{
          position: 'absolute',
          right: '12px',
          bottom: '12px',
          fontSize: '12px',
          color: 'rgba(230, 238, 252, 0.5)',
          transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s var(--micro-ease)'
        }}
      >
        ↓
      </motion.div>
    </motion.div>
  );
}