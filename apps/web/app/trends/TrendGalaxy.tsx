"use client";
import React, { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { EffectComposer, Bloom, DepthOfField, Vignette } from "@react-three/postprocessing";
import * as THREE from 'three';
import { streamlineFragment, streamlineVertex } from './shaders';

type Topic = {
  topic_id: string;
  label: string;
  momentum: number; // -1..1
  trend_state: 'rising'|'stable'|'declining';
};

function Streamlines({ topics, time, onHover, onSelect, markers, onScreenPositions, selectedId, onFocusDistance }: { topics: Topic[]; time: number; onHover?: (id:string)=>void; onSelect?: (id:string)=>void; markers?: Array<{ t:number; label?: string }>; onScreenPositions?: (pts: Array<{ x:number; y:number; id:string }>)=>void; selectedId?: string | null; onFocusDistance?: (d: number)=>void }){
  const meshRef = useRef(null as unknown as THREE.Mesh);
  const cometRef = useRef(null as unknown as THREE.Points);
  const flareGroup = useRef(null as unknown as THREE.Group);
  const reduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const count = Math.min(300, Math.max(80, topics.length));
  const { size, camera } = useThree();

  // Geometry: a thin strip (plane) used by shader to offset thickness
  const geo = useMemo(() => {
    const g = new THREE.PlaneGeometry(1, 1, 1, 32);
    // Using y as along-tube, x as cross-section
    return g;
  }, []);

  // Attributes per instance
  const { aHue, aRadius, aAngle, aSpeed, aThick } = useMemo(() => {
    const hue = new Float32Array(count);
    const radius = new Float32Array(count);
    const angle = new Float32Array(count);
    const speed = new Float32Array(count);
    const thick = new Float32Array(count);
    for (let i=0;i<count;i++){
      const t = topics[i % topics.length];
      const baseHue = t.trend_state==='rising'? 0.52 : (t.trend_state==='declining'? 0.08 : 0.78);
      hue[i] = baseHue + (Math.abs(t.momentum)*0.08);
      radius[i] = 1.8 + (i%40)*0.035;
      angle[i] = (i*0.31) % (Math.PI*2);
      // per-topic variance: faster for higher momentum, thicker when rising
      speed[i] = 0.8 + Math.max(0.05, Math.min(1.6, 1.0 + t.momentum));
      thick[i] = 0.9 + (t.trend_state==='rising'? 0.6 : t.trend_state==='declining'? -0.2 : 0.0) + Math.abs(t.momentum)*0.4;
      thick[i] = Math.max(0.5, Math.min(1.8, thick[i]));
    }
    return { aHue: hue, aRadius: radius, aAngle: angle, aSpeed: speed, aThick: thick };
  }, [topics, count]);

  const material = useMemo(() => new THREE.ShaderMaterial({
    vertexShader: streamlineVertex,
    fragmentShader: streamlineFragment,
    transparent: true,
    depthWrite: false,
    uniforms: {
      u_time: { value: 0 },
      u_speed: { value: 0.6 },
      u_thickness: { value: 0.08 },
      u_hueShift: { value: 0.0 },
    }
  }), []);

  const frameCount = useRef(0);
  useFrame((state, delta) => {
    if (reduced) return;
    material.uniforms.u_time.value = time;
    // Comet head advance via shader time; points update too
    if (cometRef.current){
      (cometRef.current.material as THREE.PointsMaterial).size = 8;
    }
    // Project comet heads to screen and report occasionally
    if (onScreenPositions && aRadius && aAngle){
      frameCount.current = (frameCount.current + 1) % 6;
      if (frameCount.current === 0){
        const pts: Array<{x:number;y:number;id:string}> = [];
        const v = new THREE.Vector3();
        for (let i=0;i<count;i++){
          const r = aRadius[i];
          const ang = aAngle[i] + time * 0.6;
          v.set(Math.sin(ang)*r, Math.cos(ang)*r*0.8, 0);
          const nv = v.clone().project(camera as any);
          const sx = (nv.x * 0.5 + 0.5) * size.width;
          const sy = (-nv.y * 0.5 + 0.5) * size.height;
          const topic = topics[i % topics.length];
          pts.push({ x: sx, y: sy, id: topic.topic_id });
        }
        onScreenPositions(pts);
      }
    }

    // Animate flares group subtly
    if (flareGroup.current){
      (flareGroup.current.rotation as any).z += delta * 0.1;
    }

    // Auto-focus DOF on selected topic if provided
    if (onFocusDistance && selectedId){
      const idx = topics.findIndex(t=> t.topic_id === selectedId);
      if (idx >= 0){
        const r = aRadius[idx % count];
        const ang = aAngle[idx % count] + time * 0.6;
        const pos = new THREE.Vector3(Math.sin(ang)*r, Math.cos(ang)*r*0.8, 0);
        // Compute depth in view space to estimate focusDistance [0..1]
        const v = pos.clone().project(camera as any);
        // Map z clip space (-1..1) to [0..1]
        const fd = THREE.MathUtils.clamp((v.z + 1.0) * 0.5, 0, 1);
        onFocusDistance(fd);
      }
    }
  });

  // Comet heads as points at vUv tip positions (approximate)
  const cometGeom = useMemo(()=>{
    const g = new THREE.BufferGeometry();
    const pts = new Float32Array(count*3);
    for (let i=0;i<count;i++){
      const r = aRadius[i];
      const ang = aAngle[i] + time * 0.6;
      const x = Math.sin(ang) * r;
      const y = Math.cos(ang) * r * 0.8;
      const z = ((i%5)-2) * 0.0; // flattened
      pts[i*3+0] = x; pts[i*3+1] = y; pts[i*3+2] = z;
    }
    g.setAttribute('position', new THREE.BufferAttribute(pts, 3));
    return g;
  }, [aRadius, aAngle, count, time]);

  return (
    <group>
      {/* Instanced streamlines */}
      <instancedMesh ref={meshRef as any} args={[geo, material, count]}>
        <instancedBufferAttribute attach="attributes-aHue" args={[aHue, 1]} />
        <instancedBufferAttribute attach="attributes-aRadius" args={[aRadius, 1]} />
        <instancedBufferAttribute attach="attributes-aAngle" args={[aAngle, 1]} />
        <instancedBufferAttribute attach="attributes-aSpeed" args={[aSpeed, 1]} />
        <instancedBufferAttribute attach="attributes-aThick" args={[aThick, 1]} />
      </instancedMesh>

      {/* Comet heads */}
      <points ref={cometRef as any} geometry={cometGeom}>
        <pointsMaterial size={6} sizeAttenuation color={'#ffffff'} transparent opacity={0.9} />
      </points>

      {/* ChangePoint flares */}
      <group ref={flareGroup as any}>
        {(markers||[]).map((m, i)=>{
          const r = 1.6 + (i%3)*0.2;
          const ang = (m.t*6.28318) + time*0.2;
          const x = Math.sin(ang)*r;
          const y = Math.cos(ang)*r*0.8;
          return (
            <mesh key={i} position={[x,y,0]}>
              <circleGeometry args={[0.08, 16]} />
              <meshBasicMaterial color={'#FFD580'} transparent opacity={0.8} blending={THREE.AdditiveBlending} />
            </mesh>
          );
        })}
      </group>
    </group>
  );
}

export function TrendGalaxy({ topics, time, onTopicHover, onTopicSelect, markers, onScreenPositions, selectedId }: {
  topics: Topic[];
  time: number;
  onTopicHover?: (id: string)=>void;
  onTopicSelect?: (id: string)=>void;
  markers?: Array<{ t:number; label?: string }>;
  onScreenPositions?: (pts: Array<{ x:number; y:number; id:string }>)=>void;
  selectedId?: string | null;
}){
  const dpr = typeof window !== 'undefined' && window.devicePixelRatio ? Math.min(window.devicePixelRatio, 1.75) : 1;
  const focusRef = useRef(0.015);
  return (
    <Canvas camera={{ position: [0,0,6], fov: 45 }} dpr={dpr}>
      <ambientLight intensity={0.6} />
      <Suspense fallback={null}>
        <Streamlines topics={topics} time={time} onHover={onTopicHover} onSelect={onTopicSelect} markers={markers} onScreenPositions={onScreenPositions} selectedId={selectedId} onFocusDistance={(d)=>{ focusRef.current = d; }} />
      </Suspense>
      <EffectComposer>
        <Bloom intensity={0.8} mipmapBlur luminanceSmoothing={0.3} />
        <DepthOfField focusDistance={focusRef.current} focalLength={0.02} bokehScale={0.8} />
        <Vignette darkness={0.35} />
      </EffectComposer>
    </Canvas>
  );
}
