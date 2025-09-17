"use client";
import React, { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
// @ts-ignore
import * as THREE from "three";
import { useLinkedStore } from "@/app/linkedStore";
import { useHeroStore } from "@/app/heroStore";

function makeRng(seed: number) {
  let t = seed % 2147483647;
  if (t <= 0) t += 2147483646;
  return () => (t = (t * 16807) % 2147483647) / 2147483647;
}

function CameraRig() {
  const { camera } = useThree();
  const progress = useHeroStore((s) => s.progress);
  useEffect(() => {
    camera.position.set(0, 0.4, 3.4);
  }, [camera]);
  useFrame(() => {
    // Dolly camera slightly as the hero pin progresses
    const z = 3.4 - progress * 0.6; // move closer
    const y = 0.4 - progress * 0.1;
    camera.position.set(0, y, z);
    // subtle fov change
    const baseFov = 55;
    // @ts-ignore
    camera.fov = baseFov + progress * 4;
    camera.updateProjectionMatrix();
  });
  return null;
}

function ParticleLayer({ count = 1200, radius = 1.4, color = "#00f0ff", seed = 1 }) {
  const ref = useRef(null as any);
  const geom = useMemo(() => new THREE.BufferGeometry(), []);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    const rand = makeRng(seed);
    for (let i = 0; i < count; i++) {
      const r = radius * (0.6 + rand() * 0.4);
      const t = rand() * Math.PI * 2;
      const p = rand() * Math.PI - Math.PI / 2;
      arr[i * 3 + 0] = Math.cos(t) * Math.cos(p) * r;
      arr[i * 3 + 1] = Math.sin(p) * r * 0.6;
      arr[i * 3 + 2] = Math.sin(t) * Math.cos(p) * r;
    }
    return arr;
  }, [count, radius, seed]);
  const mat = useMemo(() => new THREE.PointsMaterial({ size: 0.01, color, transparent: true, opacity: 0.9 }), [color]);
  useMemo(() => {
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  }, [geom, positions]);
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.y = clock.elapsedTime * 0.02;
    }
  });
  return <points ref={ref} geometry={geom} material={mat} />;
}

function Ring({ radius = 1.2, color = "#b266ff" }) {
  const ref = useRef(null as any);
  const geom = useMemo(() => new THREE.RingGeometry(radius * 0.98, radius, 64), [radius]);
  const mat = useMemo(() => new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.6, side: THREE.DoubleSide }), [color]);
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.rotation.x = Math.sin(clock.elapsedTime * 0.3) * 0.3 + Math.PI / 2;
      ref.current.rotation.z = clock.elapsedTime * 0.15;
    }
  });
  return <mesh ref={ref} geometry={geom} material={mat} />;
}

function Cluster({ id, position }: { id: string; position: [number, number, number] }) {
  const ref = useRef(null as any);
  const setHover = useLinkedStore((s) => s.setHover);
  const setSelected = useLinkedStore((s) => s.setSelected);
  const selected = useLinkedStore((s) => s.selected);
  const hover = useLinkedStore((s) => s.hover);
  const active = selected === id || hover === id;
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.y = clock.elapsedTime * 0.6;
    const base = 0.018;
    ref.current.scale.setScalar(1 + (active ? 0.25 : 0.0) + Math.sin(clock.elapsedTime * 3) * base);
  });
  const color = active ? "#00f0ff" : "#e6eefc";
  return (
    <mesh
      ref={ref}
      position={position}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHover(id);
      }}
      onPointerOut={(e) => {
        e.stopPropagation();
        setHover(null);
      }}
      onClick={(e) => {
        e.stopPropagation();
        setSelected(id);
      }}
    >
      <icosahedronGeometry args={[0.12, 0]} />
      <meshStandardMaterial color={color} emissive={active ? new THREE.Color("#00f0ff") : new THREE.Color("#000")} emissiveIntensity={active ? 0.8 : 0} metalness={0.2} roughness={0.25} />
    </mesh>
  );
}

function SceneContent() {
  const clusters: Array<{ id: string; pos: [number, number, number] }> = useMemo(
    () => [
      { id: "A", pos: [0.6, 0.2, 0.3] },
      { id: "B", pos: [-0.5, -0.1, -0.2] },
      { id: "C", pos: [0.2, -0.3, 0.5] },
      { id: "D", pos: [-0.2, 0.4, -0.5] },
    ],
    []
  );
  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[3, 3, 3]} intensity={20} color="#00f0ff" />
      <ParticleLayer count={1300} radius={1.6} color="#00f0ff" seed={1} />
      <ParticleLayer count={900} radius={1.2} color="#b266ff" seed={2} />
      <Ring radius={1.3} color="#00f0ff" />
      <Ring radius={0.9} color="#b266ff" />
      {clusters.map((c) => (
        <Cluster key={c.id} id={c.id} position={c.pos} />
      ))}
      {/* Postprocessing */}
      <EffectComposer>
        <Bloom mipmapBlur intensity={0.6} luminanceThreshold={0.15} luminanceSmoothing={0.12} radius={0.8} />
      </EffectComposer>
      <OrbitControls enablePan={false} enableZoom={false} enableRotate={true} />
      <CameraRig />
    </>
  );
}

export default function Hero3D() {
  // Reduced motion: render a static skeleton instead
  const prefersReduced = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) {
    return <div className="skeleton glass" style={{ height: 420, width: "100%" }} role="img" aria-label="Hero visualization placeholder" />;
  }
  return (
    <div className="glass" style={{ width: "100%", height: 420, position: "relative" }} role="img" aria-label="Interactive holographic hero scene">
      <Suspense fallback={<div className="skeleton" style={{ height: 420 }} />}>
        <Canvas camera={{ position: [0, 0.4, 3.4], fov: 55 }} dpr={[1, 1.75]}>
          <SceneContent />
        </Canvas>
      </Suspense>
    </div>
  );
}
 
