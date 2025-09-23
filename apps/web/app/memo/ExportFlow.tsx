"use client";
import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface ExportOptions {
  format: 'pdf' | 'ppt';
  includeProvenance: boolean;
  includeEvidence: boolean;
  template: 'executive' | 'detailed' | 'investor';
  confidenceThreshold: number;
}

interface MemoData {
  thesis: string;
  confidence: number;
  claims: Array<{
    claim_id: string;
    text: string;
    confidence: number;
    sources: string[];
    evidence_snippet: string;
  }>;
  company_name: string;
  generated_at: string;
  provenance: {
    snapshot_hash: string;
    merkle_root: string;
    signed_by: string;
  };
}

interface ExportFlowProps {
  isOpen: boolean;
  onClose: () => void;
  memo: MemoData;
  onExport: (options: ExportOptions) => Promise<void>;
}

export function ExportFlow({ isOpen, onClose, memo, onExport }: ExportFlowProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [options, setOptions] = useState({
    format: 'pdf' as const,
    includeProvenance: true,
    includeEvidence: true,
    template: 'executive' as const,
    confidenceThreshold: 0.6
  });
  const dialogRef = useRef(null as any);
  const lastFocusedRef = useRef(null as any);

  // Focus management: trap focus and restore on close
  useEffect(() => {
    if (!isOpen) return;
    lastFocusedRef.current = document.activeElement as any;

    // Focus the dialog heading or first focusable control
    const el = dialogRef.current as HTMLElement | null;
    if (el) {
      const heading = el.querySelector('#export-heading') as any;
      if (heading && (heading as any).focus) {
        (heading as any).setAttribute('tabindex', '-1');
        (heading as any).focus();
      } else {
        const focusables = el.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        ) as any;
        if (focusables && focusables.length) {
          (focusables[0] as any).focus();
        }
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

  const handleExport = async () => {
    setIsExporting(true);
    setExportProgress(0);

    try {
      // Simulate export progress
      const progressSteps = [10, 25, 50, 75, 90, 100];
      
      for (let i = 0; i < progressSteps.length; i++) {
        setExportProgress(progressSteps[i]);
        await new Promise(resolve => setTimeout(resolve, 300));
      }

      await onExport(options);
      
      // Success - auto close after a moment
      setTimeout(() => {
        onClose();
        setIsExporting(false);
        setExportProgress(0);
        setCurrentStep(1);
      }, 1500);
      
    } catch (error) {
      console.error('Export failed:', error);
      setIsExporting(false);
      setExportProgress(0);
    }
  };

  const getFilteredClaims = () => {
    return memo.claims.filter(claim => claim.confidence >= options.confidenceThreshold);
  };

  const formatFileSize = (claims: number, includeEvidence: boolean, includeProvenance: boolean) => {
    let baseSize = claims * 0.1 + 0.5; // Base size in MB
    if (includeEvidence) baseSize += claims * 0.05;
    if (includeProvenance) baseSize += 0.2;
    return `~${baseSize.toFixed(1)} MB`;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
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
          aria-labelledby="export-heading"
          onKeyDown={(e: any) => { if (e.key === 'Escape') onClose(); }}
          onClick={onClose}
        >
          <motion.div
            className="memo-glass"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            style={{
              width: '90vw',
              maxWidth: '600px',
              background: 'var(--memo-bg)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              overflow: 'hidden'
            }}
            onClick={(e: any) => e.stopPropagation()}
            ref={dialogRef}
          >
            {/* Header */}
            <div style={{
              padding: '24px 24px 16px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px'
              }}>
                <h2 id="export-heading" className="memo-title-h2">Export Memo</h2>
                <button
                  onClick={onClose}
                  disabled={isExporting}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'rgba(230, 238, 252, 0.6)',
                    fontSize: '24px',
                    cursor: isExporting ? 'not-allowed' : 'pointer',
                    padding: '8px'
                  }}
                >
                  ×
                </button>
              </div>

              {/* Progress indicator */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '12px',
                color: 'rgba(230, 238, 252, 0.6)'
              }}>
                <span style={{ color: currentStep >= 1 ? 'var(--aurora-cyan)' : undefined }}>
                  1. Format
                </span>
                <span style={{ color: currentStep >= 2 ? 'var(--aurora-cyan)' : undefined }}>
                  2. Options
                </span>
                <span style={{ color: currentStep >= 3 ? 'var(--aurora-cyan)' : undefined }}>
                  3. Preview
                </span>
              </div>
            </div>

            {/* Content */}
            <div style={{ padding: '24px', minHeight: '400px' }}>
              {/* Step 1: Format Selection */}
              {currentStep === 1 && (
                <div>
                  <h3 style={{ marginBottom: '16px', color: 'var(--starlight)', fontSize: '18px' }}>
                    Choose Export Format
                  </h3>
                  
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {[
                      {
                        format: 'pdf' as const,
                        title: 'PDF Report',
                        description: 'Printable document with embedded provenance',
                        icon: '📄'
                      },
                      {
                        format: 'ppt' as const,
                        title: 'PowerPoint Deck',
                        description: 'Presentation-ready slides with visuals',
                        icon: '📊'
                      }
                    ].map((item) => (
                      <div
                        key={item.format}
                        className="memo-page"
                        style={{
                          padding: '20px',
                          cursor: 'pointer',
                          border: options.format === item.format 
                            ? '2px solid var(--aurora-cyan)' 
                            : '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: '8px',
                          background: options.format === item.format
                            ? 'rgba(0, 240, 255, 0.05)'
                            : undefined
                        }}
                        onClick={() => setOptions((prev: any) => ({ ...prev, format: item.format }))}
                      >
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                          <div style={{ fontSize: '24px' }}>{item.icon}</div>
                          <div style={{ flex: 1 }}>
                            <h4 style={{ margin: '0 0 8px', color: 'var(--starlight)', fontSize: '16px' }}>
                              {item.title}
                            </h4>
                            <p className="memo-body" style={{ margin: '0', fontSize: '14px', opacity: 0.8 }}>
                              {item.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 2: Options */}
              {currentStep === 2 && (
                <div>
                  <h3 style={{ marginBottom: '16px', color: 'var(--starlight)', fontSize: '18px' }}>
                    Export Options
                  </h3>

                  <div style={{ display: 'grid', gap: '20px' }}>
                    {/* Template selection */}
                    <div>
                      <label className="memo-label" style={{ display: 'block', marginBottom: '8px' }}>
                        Template Style
                      </label>
                      <div style={{ display: 'grid', gap: '8px' }}>
                        {[
                          { key: 'executive', label: 'Executive Summary', desc: 'High-level insights only' },
                          { key: 'detailed', label: 'Detailed Analysis', desc: 'Full claims and evidence' },
                          { key: 'investor', label: 'Investor Brief', desc: 'Financial focus with risk assessment' }
                        ].map((template) => (
                          <label
                            key={template.key}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '12px',
                              padding: '12px',
                              background: 'rgba(255, 255, 255, 0.03)',
                              borderRadius: '6px',
                              cursor: 'pointer'
                            }}
                          >
                            <input
                              type="radio"
                              name="template"
                              value={template.key}
                              checked={options.template === template.key}
                              onChange={(e: any) => setOptions((prev: any) => ({ 
                                ...prev, 
                                template: e.target.value
                              }))}
                              style={{ marginRight: '8px' }}
                            />
                            <div>
                              <div className="memo-body" style={{ fontWeight: '500' }}>
                                {template.label}
                              </div>
                              <div className="memo-body" style={{ fontSize: '12px', opacity: 0.7 }}>
                                {template.desc}
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Include options */}
                    <div>
                      <div className="memo-label" style={{ marginBottom: '12px' }}>
                        Include in Export
                      </div>
                      <div style={{ display: 'grid', gap: '8px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={options.includeEvidence}
                            onChange={(e: any) => setOptions((prev: any) => ({ 
                              ...prev, 
                              includeEvidence: e.target.checked 
                            }))}
                          />
                          <span className="memo-body">Supporting Evidence</span>
                        </label>
                        
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={options.includeProvenance}
                            onChange={(e: any) => setOptions((prev: any) => ({ 
                              ...prev, 
                              includeProvenance: e.target.checked 
                            }))}
                          />
                          <span className="memo-body">Cryptographic Provenance</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Preview */}
              {currentStep === 3 && (
                <div>
                  <h3 style={{ marginBottom: '16px', color: 'var(--starlight)', fontSize: '18px' }}>
                    Export Preview
                  </h3>

                  <div className="memo-page" style={{ padding: '20px' }}>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                      gap: '16px',
                      marginBottom: '20px'
                    }}>
                      <div>
                        <div className="memo-label" style={{ marginBottom: '4px' }}>Format</div>
                        <div className="memo-body" style={{ textTransform: 'uppercase' }}>
                          {options.format}
                        </div>
                      </div>
                      
                      <div>
                        <div className="memo-label" style={{ marginBottom: '4px' }}>Template</div>
                        <div className="memo-body" style={{ textTransform: 'capitalize' }}>
                          {options.template}
                        </div>
                      </div>
                      
                      <div>
                        <div className="memo-label" style={{ marginBottom: '4px' }}>Claims</div>
                        <div className="memo-body">
                          {getFilteredClaims().length} / {memo.claims.length}
                        </div>
                      </div>
                      
                      <div>
                        <div className="memo-label" style={{ marginBottom: '4px' }}>Est. Size</div>
                        <div className="memo-body">
                          {formatFileSize(
                            getFilteredClaims().length, 
                            options.includeEvidence, 
                            options.includeProvenance
                          )}
                        </div>
                      </div>
                    </div>

                    {isExporting && (
                      <div style={{
                        padding: '16px',
                        background: 'rgba(0, 240, 255, 0.1)',
                        border: '1px solid rgba(0, 240, 255, 0.3)',
                        borderRadius: '6px'
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          marginBottom: '8px'
                        }}
                        aria-live="polite"
                        role="status"
                        >
                          <div style={{
                            width: '16px',
                            height: '16px',
                            border: '2px solid var(--aurora-cyan)',
                            borderTop: '2px solid transparent',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite'
                          }} />
                          <span className="memo-body">
                            Generating {options.format.toUpperCase()}...
                          </span>
                        </div>
                        <div style={{
                          height: '4px',
                          background: 'rgba(255, 255, 255, 0.1)',
                          borderRadius: '2px',
                          overflow: 'hidden'
                        }}>
                          <div
                            style={{
                              height: '100%',
                              background: 'var(--aurora-cyan)',
                              width: `${exportProgress}%`,
                              transition: 'width 0.3s ease'
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div style={{
              padding: '16px 24px',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                {currentStep > 1 && (
                  <button
                    onClick={() => setCurrentStep((prev: any) => prev - 1)}
                    disabled={isExporting}
                    style={{
                      background: 'none',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      color: 'var(--starlight)',
                      padding: '8px 16px',
                      borderRadius: '6px',
                      cursor: isExporting ? 'not-allowed' : 'pointer'
                    }}
                  >
                    Back
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={onClose}
                  disabled={isExporting}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: 'var(--starlight)',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    cursor: isExporting ? 'not-allowed' : 'pointer'
                  }}
                >
                  Cancel
                </button>
                
                {currentStep < 3 ? (
                  <button
                    onClick={() => setCurrentStep((prev: any) => prev + 1)}
                    style={{
                      background: 'var(--aurora-cyan)',
                      color: 'var(--bg-00)',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '6px',
                      cursor: 'pointer'
                    }}
                  >
                    Next
                  </button>
                ) : (
                  <button
                    onClick={handleExport}
                    disabled={isExporting}
                    style={{
                      background: isExporting 
                        ? 'rgba(0, 240, 255, 0.5)' 
                        : 'var(--aurora-cyan)',
                      color: 'var(--bg-00)',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '6px',
                      cursor: isExporting ? 'not-allowed' : 'pointer'
                    }}
                  >
                    {isExporting ? 'Exporting...' : 'Export'}
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}