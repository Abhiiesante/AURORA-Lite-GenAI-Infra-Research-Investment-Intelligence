"use client";
import React, { Suspense, useEffect, useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';

type Slab = { id: string; name: string; color: string };

function BalanceBeam({ torque, maxAngle=12 }: { torque: number; maxAngle?: number }){
  const beamRef = useRef(null as unknown as THREE.Mesh);
  const angleDeg = useRef(0);
  const prefersReduced = useMemo(()=>{
    if (typeof window === 'undefined') return false;
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }, []);
  useEffect(()=>{
    const k = 6; // mapping from torque to degrees
    const target = Math.max(-maxAngle, Math.min(maxAngle, k * torque));
    if (prefersReduced){
      angleDeg.current = target;
      if (beamRef.current){ beamRef.current.rotation.z = THREE.MathUtils.degToRad(target); }
      return;
    }
    gsap.to(angleDeg, { current: target, duration: 0.22, ease: 'power2.out', onUpdate: ()=>{
      if (beamRef.current){ beamRef.current.rotation.z = THREE.MathUtils.degToRad(angleDeg.current); }
    }});
  }, [torque, maxAngle, prefersReduced]);
  return (
    <mesh ref={beamRef as any} position={[0,0,0.2]}>
      <boxGeometry args={[4.4, 0.08, 0.08]} />
      <meshStandardMaterial color={'#1b2333'} metalness={0.1} roughness={0.7} />
    </mesh>
  );
}

function Fulcrum(){
  return (
    <mesh position={[0, -0.15, 0]}>
      <cylinderGeometry args={[0.12, 0.2, 0.3, 24]} />
      <meshStandardMaterial color={'#0d1422'} metalness={0.2} roughness={0.8} />
    </mesh>
  );
}

function Plane(){
  return (
    <mesh rotation={[-Math.PI/2, 0, 0]}>
      <planeGeometry args={[7, 4, 1, 1]} />
      <meshStandardMaterial color={'#0A0F1A'} metalness={0.05} roughness={0.95} />
    </mesh>
  );
}

function SlabBlock({ position, color, label }: { position:[number,number,number]; color:string; label:string }){
  const matRef = useRef(null as unknown as THREE.ShaderMaterial);
  const uniforms = useMemo(()=> ({
    u_color: { value: new THREE.Color(color) },
    u_rimColor: { value: new THREE.Color('#8fb3ff') },
    u_rimPower: { value: 1.8 },
    u_rimStrength: { value: 0.35 },
  }), [color]);
  const vertex = `
    varying vec3 vNormal;
    varying vec3 vWorldPos;
    void main(){
      vNormal = normalize(normalMatrix * normal);
      vec4 wp = modelMatrix * vec4(position,1.0);
      vWorldPos = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }
  `;
  const fragment = `
    uniform vec3 u_color;
    uniform vec3 u_rimColor;
    uniform float u_rimPower;
    uniform float u_rimStrength;
    varying vec3 vNormal;
    varying vec3 vWorldPos;
    void main(){
      vec3 N = normalize(vNormal);
      vec3 V = normalize(cameraPosition - vWorldPos);
      float rim = pow(1.0 - max(dot(N,V), 0.0), u_rimPower);
      vec3 base = u_color;
      vec3 col = mix(base, u_rimColor, rim * u_rimStrength);
      gl_FragColor = vec4(col, 1.0);
    }
  `;
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={[0.9, 0.12, 0.6]} />
        <shaderMaterial ref={matRef as any} args={[{ uniforms, vertexShader: vertex, fragmentShader: fragment }]} />
      </mesh>
      {/* lightweight label plane */}
      <mesh position={[0, 0.1, 0]}>
        <planeGeometry args={[0.9, 0.2]} />
        <meshBasicMaterial color={'#111826'} />
      </mesh>
    </group>
  );
}

export function CompareCanvas({ torque, slabs }: { torque: number; slabs: Slab[] }){
  const dpr = typeof window !== 'undefined' && window.devicePixelRatio ? Math.min(Math.max(1, window.devicePixelRatio), 1.75) : 1;
  const prefersReduced = typeof window !== 'undefined' && window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false;
  return (
    <Canvas camera={{ position: [0,1.8,4.4], fov: 45 }} dpr={dpr}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[2,3,2]} intensity={0.6} />
      <Suspense fallback={null}>
        <Plane />
        <Fulcrum />
        <BalanceBeam torque={torque} />
        {slabs.map((s, i)=> (
          <SlabBlock key={s.id} position={i===0?[ -1.4, 0, 0 ]: [1.4, 0, 0]} color={s.color} label={s.name} />
        ))}
        {!prefersReduced && (
          <EffectComposer>
            <Bloom intensity={0.2} luminanceThreshold={0.4} luminanceSmoothing={0.2} />
            <Vignette eskil={false} offset={0.1} darkness={0.65} />
          </EffectComposer>
        )}
      </Suspense>
    </Canvas>
  );
}
