"use client";
import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import NavBar from "@/components/NavBar";
import dynamic from "next/dynamic";
const Hero3D = dynamic(() => import("@/components/Hero3D"), { ssr: false, loading: () => <div className="skeleton glass" style={{ height: 420 }} /> });
import LinkedAreaChart from "@/components/LinkedAreaChart";
import { KPIRow } from "@/components/KPI";
import QuickActions from "@/components/QuickActions";
import CompanyGrid from "@/components/CompanyGrid";
import SystemStatusStrip from "@/components/SystemStatusStrip";
import FloatingOrb from "@/components/FloatingOrb";
import MiniConstellation from "@/components/MiniConstellation";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
const RadialGauge3D = dynamic(()=> import("@/components/RadialGauge3D"), { ssr:false });
import { useHeroStore } from "@/app/heroStore";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const containerRef = useRef(null as HTMLDivElement | null);
  useEffect(()=>{
    const prefersReduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;
    if (typeof window !== 'undefined') { gsap.registerPlugin(ScrollTrigger); }
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>('.section').forEach((el, i) => {
        gsap.fromTo(el, { y: 18, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power2.out', scrollTrigger: { trigger: el, start: 'top 80%' } });
      });
      // Pin hero container for the first segment and scale down slightly as content scrolls
      const hero = document.querySelector('.hero-pin') as HTMLElement | null;
      const vignette = hero?.querySelector('.hero-vignette') as HTMLElement | null;
      const avatar = document.querySelector('.navbar .avatar') as HTMLElement | null;
      if (hero) {
        ScrollTrigger.create({
          trigger: hero,
          start: 'top top',
          end: '+=60%',
          pin: true,
          scrub: true,
          onUpdate: (self) => {
            const t = self.progress; // 0..1
            gsap.to(hero, { scale: 1 - t*0.08, filter: `saturate(${1 - t*0.2})`, duration: 0.1 });
            if (vignette) gsap.to(vignette, { opacity: t, duration: 0.1 });
            if (avatar) gsap.to(avatar, { scale: 0.9 - t*0.2, boxShadow: `0 0 ${12*(1-t)}px rgba(0,240,255,0.5)`, duration: 0.1, transformOrigin: 'center center' });
            // broadcast to hero store for camera dolly
            try { (useHeroStore.getState().setProgress)(t); } catch {}
          },
          onLeave: () => {
            // Leaving pin (scrolling down): fade vignette out and keep compact avatar
            if (vignette) gsap.to(vignette, { opacity: 0, duration: 0.2, ease: 'power2.out' });
            if (avatar) gsap.to(avatar, { scale: 0.8, boxShadow: '0 0 0px rgba(0,240,255,0.0)', duration: 0.2, ease: 'power2.out' });
          },
          onEnterBack: () => {
            // Re-entering pin from below (scrolling up): reset states to start clean
            if (vignette) gsap.set(vignette, { opacity: 0 });
            if (avatar) gsap.to(avatar, { scale: 0.9, boxShadow: '0 0 12px rgba(0,240,255,0.5)', duration: 0.2 });
          }
        });
      }
    }, containerRef);
    return () => ctx.revert();
  },[]);
  const { data } = useQuery({
    queryKey: ["companies"],
    queryFn: async () => (await axios.get(`${api}/companies/`)).data,
  });

  const companies = (data || []) as any[];

  return (
    <main ref={containerRef}>
      <NavBar />
      <div className="container">
        <div className="section hero-pin">
          <h1 className="headline neon" style={{ fontSize: 42, margin: "12px 0 10px" }}>Aurora Command Deck</h1>
          <div style={{ opacity: 0.75, marginBottom: 12 }}>GenAI Infra Research & Investment Intelligence</div>
          <Hero3D />
          <div className="hero-vignette" aria-hidden="true" />
        </div>

        <div className="aurora" />

        <div className="section">
          <KPIRow />
        </div>
        <div className="section" style={{ display:'flex', gap:14 }}>
          <RadialGauge3D value={0.72} color="#00f0ff" label="Signal Health" />
          <RadialGauge3D value={0.54} color="#b266ff" label="Coverage" />
          <RadialGauge3D value={0.86} color="#ff7a00" label="Anomaly Risk" />
        </div>
        <div className="section">
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Trends (Linked to Hero)</div>
          <LinkedAreaChart />
        </div>

        <div className="section row">
          <div className="col" style={{ flex: 1 }}>
            <div className="glass" style={{ padding: 14 }}>
              <div style={{ fontWeight: 600, marginBottom: 8 }}>Quick Actions</div>
              <QuickActions />
            </div>
            <div style={{ marginTop: 14 }}>
              <MiniConstellation />
            </div>
          </div>
          <div className="col" style={{ flex: 3 }}>
            <div style={{ display: 'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 8 }}>
              <div style={{ fontWeight: 600 }}>Companies</div>
              <div className="row">
                <button className="glass" onClick={() => axios.post(`${api}/health/seed`).then(()=>alert('Seeded')).catch(()=>alert('Seed failed'))}>
                  Seed
                </button>
                <button className="glass" onClick={() => axios.post(`${api}/health/seed-rag`).then(()=>alert('Seeded RAG')).catch(()=>alert('RAG seed failed'))}>
                  Seed RAG
                </button>
              </div>
            </div>
            <CompanyGrid companies={companies} />
          </div>
        </div>
      </div>
      <div className="aurora" />

      <SystemStatusStrip />
      <FloatingOrb />
    </main>
  );
}
