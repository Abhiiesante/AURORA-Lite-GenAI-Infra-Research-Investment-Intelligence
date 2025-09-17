"use client";
import React, { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
// Use dynamic import type to avoid hard dependency on types
// @ts-ignore
import * as THREE from "three";

function Points() {
  const ref = useRef(null as any);
  const geom = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const N = 400;
    const pos = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      pos[i * 3 + 0] = (Math.random() - 0.5) * 2;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 2;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 2;
    }
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    return g;
  }, []);
  const mat = useMemo(() => new THREE.PointsMaterial({ size: 0.015, color: "#00f0ff" }), []);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y += 0.0015;
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
    }
  });
  return <points ref={ref} geometry={geom} material={mat} />;
}

export default function MiniConstellation() {
  return (
    <div style={{ width: "100%", height: 160 }} className="glass">
      <Canvas camera={{ position: [0, 0, 3] }}>
        <ambientLight intensity={0.6} />
        <Points />
      </Canvas>
    </div>
  );
}
