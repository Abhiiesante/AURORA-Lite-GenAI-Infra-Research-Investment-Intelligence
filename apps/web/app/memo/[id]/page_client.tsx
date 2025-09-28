"use client";
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import gsap from "gsap";
import { ConfidenceGauge } from "../ConfidenceGauge";
import { ClaimCard } from "../ClaimCard";
import { ProvenanceModal } from "../ProvenanceModal";
import { ExportFlow } from "../ExportFlow";
import "../memo-tokens.css";

const pageVariants = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16,0.84,0.24,1] } } };
const heroVariants = { initial: { opacity: 0, scale: 0.95 }, animate: { opacity: 1, scale: 1, transition: { duration: 0.8, ease: [0.16,0.84,0.24,1], delay: 0.1 } } };
const claimsVariants = { initial: { opacity: 0, y: 40 }, animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16,0.84,0.24,1], delay: 0.3, staggerChildren: 0.1 } } };

export default function MemoClient(){
  const params = useParams();
  const companyId = params.id as string;
  const heroRef = useRef(null as any);
  const claimsRef = useRef(null as any);
  const [memo, setMemo] = useState(null as any);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedClaimId, setExpandedClaimId] = useState(null as string | null);
  const [provenanceOpen, setProvenanceOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  useEffect(() => { loadMemo(); }, [companyId]);
  useEffect(() => { const prefersReduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; if (prefersReduced) return; const tl = gsap.timeline({ defaults:{ ease:'power2.out' } }); if (heroRef.current) { tl.fromTo(heroRef.current, { opacity:0, y:20 }, { opacity:1, y:0, duration:0.6 }); } if (claimsRef.current) { tl.fromTo(claimsRef.current, { opacity:0, y:20 }, { opacity:1, y:0, duration:0.6 }, '-=0.2'); } return () => { tl.kill(); }; }, []);

  const loadMemo = async () => { try { setLoading(true); const response = await fetch(`/api/memo/${companyId}`); if (response.ok) { const data = await response.json(); setMemo(data); } else { await generateMemo(); } } catch(e){ console.error('Error loading memo', e); await generateMemo(); } finally { setLoading(false); } };
  const generateMemo = async () => { try { setGenerating(true); const response = await fetch('/api/memo/generate', { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ companyId: `company:${companyId}`, template:'investment' }) }); if (!response.ok) throw new Error('Failed to generate memo'); const data = await response.json(); setMemo(data); } catch(e){ console.error('Error generating memo', e); /* no static fallback: remain in error state for dynamic integrity */ } finally { setGenerating(false); } };

  const handleClaimEdit = (claimId:string, newText:string) => { if(!memo) return; setMemo((prev:any) => prev ? { ...prev, claims: prev.claims.map((c:any)=> c.claim_id===claimId ? { ...c, text:newText } : c) } : prev); };
  const handleExport = async (options:any) => { if(!memo) return; console.log('Export', options); await new Promise(r=>setTimeout(r,1500)); };

  useEffect(()=>{ const handler = (e:KeyboardEvent)=>{ if(!memo) return; if((e.ctrlKey||e.metaKey) && e.key==='p'){ e.preventDefault(); setProvenanceOpen(true);} if((e.ctrlKey||e.metaKey) && e.key==='e'){ e.preventDefault(); setExportOpen(true);} if(e.key==='Escape'){ setProvenanceOpen(false); setExportOpen(false); setExpandedClaimId(null);} }; window.addEventListener('keydown', handler); return ()=>window.removeEventListener('keydown', handler); }, [memo]);

  if (loading && !generating) return <Centered status text="Loading memo..." />;
  if (generating) return <Centered spinner text="Generating Investment Memo" sub="Analyzing company data and market signals..." />;
  if (!memo) return <Centered error text="Failed to load memo" />;

  return (
    <motion.div variants={pageVariants} initial="initial" animate="animate" exit={{ opacity:0, y:-10, transition:{ duration:0.2 } }} style={{ minHeight:'100vh', background:'var(--bg-00)', padding:0 }}>
      <motion.section variants={heroVariants} initial="initial" animate="animate" style={{ background:'linear-gradient(135deg, var(--bg-00) 0%, var(--bg-01) 100%)', padding:'80px 0 60px', position:'relative', overflow:'hidden' }} ref={heroRef} aria-labelledby="memo-hero-heading">
        <div style={{ position:'absolute', inset:0, backgroundImage:'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)', backgroundSize:'20px 20px', opacity:0.1 }} />
        <div style={{ maxWidth:'1200px', margin:'0 auto', padding:'0 24px', position:'relative', zIndex:1 }}>
          <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:'60px', alignItems:'center' }}>
            <div>
              <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.2, duration:0.5 }} style={{ marginBottom:'16px' }}>
                <div style={{ display:'inline-block', padding:'6px 16px', background:'rgba(0, 240, 255, 0.15)', border:'1px solid rgba(0, 240, 255, 0.3)', borderRadius:'20px', fontSize:'14px', color:'var(--aurora-cyan)', fontWeight:500, marginBottom:'24px' }}>Investment Memo</div>
              </motion.div>
              <motion.h1 className="memo-title-h1" id="memo-hero-heading" initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.3, duration:0.5 }} style={{ marginBottom:'24px' }}>{memo.company_name}</motion.h1>
              <motion.div className="memo-body" initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.4, duration:0.5 }} style={{ fontSize:'20px', lineHeight:1.6, maxWidth:'600px', opacity:0.9 }}>{memo.thesis}</motion.div>
              <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.5, duration:0.5 }} style={{ display:'flex', gap:'12px', marginTop:'32px' }}>
                <motion.button onClick={()=>setProvenanceOpen(true)} style={{ background:'rgba(255, 255, 255, 0.1)', border:'1px solid rgba(255, 255, 255, 0.2)', color:'var(--starlight)', padding:'12px 20px', borderRadius:'8px', cursor:'pointer', fontSize:'14px', fontWeight:500, transition:'all 0.2s var(--memo-ease)' }} whileHover={{ y:-2, backgroundColor:'rgba(255, 255, 255, 0.15)' }} whileTap={{ scale:0.98 }}>View Provenance ⌘P</motion.button>
                <motion.button onClick={()=>setExportOpen(true)} style={{ background:'var(--aurora-cyan)', border:'none', color:'var(--bg-00)', padding:'12px 20px', borderRadius:'8px', cursor:'pointer', fontSize:'14px', fontWeight:600, transition:'all 0.2s var(--memo-ease)' }} whileHover={{ y:-2, backgroundColor:'#00D4ED' }} whileTap={{ scale:0.98 }}>Export Memo ⌘E</motion.button>
              </motion.div>
            </div>
            <motion.div initial={{ opacity:0, scale:0.8 }} animate={{ opacity:1, scale:1 }} transition={{ delay:0.6, duration:0.6 }} style={{ display:'flex', justifyContent:'center', alignItems:'center', height:'300px' }}>
              <ConfidenceGauge confidence={memo.confidence} />
            </motion.div>
          </div>
        </div>
      </motion.section>
      <motion.section variants={claimsVariants} initial="initial" animate="animate" style={{ maxWidth:'800px', margin:'0 auto', padding:'60px 24px' }} ref={claimsRef} aria-label="Investment claims">
        <motion.h2 className="memo-title-h2" style={{ marginBottom:'32px', textAlign:'center' }}>Investment Claims ({memo.claims.length})</motion.h2>
        <div>{memo.claims.map((claim:any, index:number)=>(
          <motion.div key={claim.claim_id} variants={{ initial:{ opacity:0, y:20 }, animate:{ opacity:1, y:0, transition:{ delay:index*0.1, duration:0.4, ease:[0.16,0.84,0.24,1] } } }}>
            <ClaimCard claim={claim} index={index} expanded={expandedClaimId===claim.claim_id} onExpand={()=>setExpandedClaimId(expandedClaimId===claim.claim_id?null:claim.claim_id)} onEdit={handleClaimEdit} />
          </motion.div>))}</div>
      </motion.section>
      <ProvenanceModal isOpen={provenanceOpen} onClose={()=>setProvenanceOpen(false)} provenance={memo.provenance} />
      <ExportFlow isOpen={exportOpen} onClose={()=>setExportOpen(false)} memo={memo} onExport={handleExport} />
    </motion.div>
  );
}

function Centered({ spinner, text, sub, error, status }: { spinner?: boolean; text: string; sub?: string; error?: boolean; status?: boolean }){
  return (
    <div style={{ minHeight:'100vh', background:'var(--bg-00)', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:'20px' }} role={status?"status":undefined} aria-live={status?"polite":undefined}>
      {spinner && <motion.div animate={{ rotate:360 }} transition={{ duration:2, repeat:Infinity, ease:"linear" }} style={{ width:40, height:40, border:'3px solid rgba(0, 240, 255, 0.3)', borderTop:'3px solid var(--aurora-cyan)', borderRadius:'50%' }} />}
      <div style={{ fontSize:18, color:error?'#f66':'var(--starlight)', textAlign:'center', opacity:0.85 }}>{text}{sub && <div style={{ fontSize:14, opacity:0.7, marginTop:8 }}>{sub}</div>}</div>
    </div>
  );
}
