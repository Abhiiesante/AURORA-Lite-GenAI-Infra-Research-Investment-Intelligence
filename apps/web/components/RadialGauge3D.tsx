"use client";
import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
// @ts-ignore
import * as THREE from "three";

function GaugeMesh({ target = 0.7, color = "#00f0ff" }: { target?: number; color?: string }){
  const ref = useRef(null as any);
  const [geom, setGeom] = useState(() => new THREE.RingGeometry(0.55, 0.75, 96, 1, Math.PI*1.5, Math.PI*0.0001));
  const mat = useMemo(() => new THREE.MeshStandardMaterial({ color, emissive: new THREE.Color(color), emissiveIntensity: 0.5, metalness: 0.2, roughness: 0.25, side: THREE.DoubleSide }), [color]);
  const bg = useMemo(() => new THREE.MeshBasicMaterial({ color: "#1b2436", transparent: true, opacity: 0.8, side: THREE.DoubleSide }), []);
  const bgGeom = useMemo(() => new THREE.RingGeometry(0.55, 0.75, 96), []);
  const progress = useRef(0);
  useFrame((_, dt) => {
    // Animate towards target
    progress.current = THREE.MathUtils.lerp(progress.current, target, Math.min(1, dt * 4));
    const length = Math.max(0.0001, Math.PI * 2 * progress.current);
    const start = Math.PI * 1.5; // start at the bottom
    const g = new THREE.RingGeometry(0.55, 0.75, 96, 1, start, length);
  setGeom((old: THREE.RingGeometry) => { old.dispose(); return g; });
    if (ref.current) {
      ref.current.rotation.z = 0.0;
    }
  });
  return (
    <group>
      <mesh geometry={bgGeom} material={bg} />
      <mesh ref={ref} geometry={geom} material={mat} position={[0,0,0.01]} />
      <pointLight position={[2,2,2]} intensity={8} color={color} />
    </group>
  );
}

export default function RadialGauge3D({ value = 0.7, color = "#00f0ff", label }:{ value?: number; color?: string; label?: string }){
  const prefersReduced = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) {
    return (
      <div className="glass" style={{ width: 160, height: 160, display:'flex', alignItems:'center', justifyContent:'center', flexDirection:'column' }} aria-label={`${label||'Gauge'} ${Math.round(value*100)} percent`}>
        <div style={{ fontFamily:'"Roboto Mono", ui-monospace', fontSize: 22 }}>{Math.round(value*100)}%</div>
        <div style={{ opacity:0.7, fontSize:12 }}>{label}</div>
      </div>
    );
  }
  return (
    <div className="glass" style={{ width: 160, height: 160, position:'relative', display:'flex', alignItems:'center', justifyContent:'center', flexDirection:'column' }} aria-label={`${label||'Gauge'} ${Math.round(value*100)} percent`}>
      <Suspense fallback={<div className="skeleton" style={{ position:'absolute', inset:0 }} />}> 
        <Canvas camera={{ position: [0,0,3] }} dpr={[1, 1.75]}>
          <ambientLight intensity={0.6} />
          <GaugeMesh target={value} color={color} />
        </Canvas>
      </Suspense>
      <div style={{ position:'absolute', bottom:12, textAlign:'center' }}>
        <div style={{ fontFamily:'"Roboto Mono", ui-monospace', fontSize: 18 }}>{Math.round(value*100)}%</div>
        <div style={{ opacity:0.7, fontSize:12 }}>{label}</div>
      </div>
    </div>
  );
}
