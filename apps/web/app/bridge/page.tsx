"use client";
import "./tokens.css";
import BridgeHero from "./BridgeHero";
import KPITile from "./KPITile";
import FAB from "./FAB";
import { useKPIs, useNodes } from "./hooks";
import LeftRail from "./LeftRail";
import RadialMenu from "./RadialMenu";
import { useReducedMotion } from "./useReducedMotion";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
gsap.registerPlugin(ScrollTrigger);

export default function BridgePage() {
  const { data: kpisData, isLoading: kpisLoading, error: kpisError } = useKPIs();
  const { data: nodesData, isLoading: nodesLoading, error: nodesError } = useNodes();

  const nodes = nodesData?.nodes ?? [];
  const clusters = nodesData?.clusters ?? [];
  const kpis = kpisData ?? null;
  const reduced = useReducedMotion();
  const [menuOpen, setMenuOpen] = useState(false);
  const heroRef = useRef(null as unknown as HTMLElement | null);

  useEffect(() => {
    if (reduced || !heroRef.current) return;
    const el = heroRef.current;
    const ctx = gsap.context(() => {
      const st = ScrollTrigger.create({
        trigger: el,
        start: "top top",
        end: "+=25%",
        pin: true,
      });
      return () => st.kill();
    });
    return () => ctx.revert();
  }, [reduced]);
  return (
    <main style={{ background: "var(--bg-01)", minHeight: "100vh" }}>
      <section ref={heroRef} className="hero" style={{ maxWidth: 1600, margin: "0 auto" }}>
        <BridgeHero
          nodes={nodes as any}
          clusters={clusters as any}
          onSceneReady={(api)=>{
            if (reduced) return;
            // Simple scroll-linked dolly: z 6 -> 4 across hero pin duration
            const state = { z: 6 };
            const tween = gsap.fromTo(state, { z: 6 }, { z: 4, ease: "power2.out",
              scrollTrigger: {
                trigger: heroRef.current!, start: "top top", end: "+=25%", scrub: 0.3
              }, onUpdate: () => { api.animateCameraZ(state.z); }
            });
            return () => tween.kill();
          }}
          config={{
            bloom: reduced ? 0.2 : 0.75,
            fresnelPower: 2.4,
            particleCount: reduced ? 1200 : 8000,
            enablePostprocessing: !reduced,
          }}
        />
        {(nodesLoading || nodesError) && (
          <div role="status" aria-live="polite" style={{position:"absolute", top:16, right:16, padding:"6px 10px", background:"rgba(0,0,0,0.5)", border:"1px solid rgba(255,255,255,0.15)", borderRadius:8, color:"var(--starlight)", fontSize:12}}>
            {nodesLoading ? "Loading scene…" : "Scene data unavailable"}
          </div>
        )}
      </section>
      <section style={{ display: "flex", gap: 24, justifyContent: "center", marginTop: -40, flexWrap: "wrap" }}>
        {kpisLoading && (
          <div role="status" aria-live="polite" style={{ color:"var(--starlight)", opacity:0.8, fontSize:14 }}>Loading KPIs…</div>
        )}
        {kpisError && (
          <div role="status" aria-live="polite" style={{ color:"var(--starlight)", opacity:0.8, fontSize:14 }}>KPI data unavailable</div>
        )}
        {kpis && (
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }}
            variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.08 } } }}
            style={{ display: "flex", gap: 24, flexWrap: "wrap", justifyContent: "center" }}>
            {[
              <KPITile key="k1" label="Signal Score" value={kpis.signalScore} deltaPercent={+2.1} status="ok" />,
              <KPITile key="k2" label="Market Momentum" value={kpis.marketMomentum} deltaPercent={+12.4} status="ok" />,
              <KPITile key="k3" label="Top Alert" value={kpis.topAlert.title} status="alert" />,
              <KPITile key="k4" label="Deal Pipeline" value={kpis.dealPipeline} deltaPercent={-1.8} status="warn" />
            ].map((tile, i) => (
              <motion.div key={i} variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.2, 0.9, 0.3, 1] } } }}>
                {tile}
              </motion.div>
            ))}
          </motion.div>
        )}
      </section>
      <div role="status" aria-live="polite" style={{position:"fixed", left:0, right:0, bottom:0, height:32, display:"flex", alignItems:"center", gap:12, padding:"0 16px", background:"rgba(0,0,0,0.4)", backdropFilter:"blur(8px)", WebkitBackdropFilter:"blur(8px)"}}>
        <strong style={{color:"var(--aurora-cyan)", fontSize:12}}>Live</strong>
        <span style={{fontSize:12, opacity:0.9}}>Vector DB hiring surge • Deal flow steady • Momentum +12.4%</span>
        <button aria-label="Pause ticker" style={{marginLeft:"auto", fontSize:12, background:"transparent", color:"var(--starlight)", border:"1px solid rgba(255,255,255,0.2)", borderRadius:8, padding:"2px 8px"}}>Pause</button>
      </div>
      <LeftRail actions={[
        { id: "watchlist", label: "New Watchlist", ariaLabel: "Create new watchlist" },
        { id: "compare", label: "Compare", badge: "Beta" },
        { id: "memo", label: "Generate Memo" },
        { id: "alerts", label: "Alerts" },
        { id: "snapshot", label: "Snapshot" },
      ]} />
      <FAB onClick={() => setMenuOpen(true)} />
      <RadialMenu open={menuOpen} onClose={() => setMenuOpen(false)} items={[
        { id: "watchlist", label: "W", onSelect: ()=>{} },
        { id: "compare", label: "C", onSelect: ()=>{} },
        { id: "memo", label: "M", onSelect: ()=>{} },
        { id: "alerts", label: "A", onSelect: ()=>{} },
        { id: "snapshot", label: "S", onSelect: ()=>{} },
      ]} />
    </main>
  );
}
