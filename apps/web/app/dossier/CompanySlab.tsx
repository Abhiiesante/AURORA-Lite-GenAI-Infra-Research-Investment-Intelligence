// @ts-nocheck
"use client";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { useMemo, useRef } from "react";

export type CompanySlabProps = {
  logoUrl?: string;
  signalScore?: number; // 0..100
  healthColor?: string; // CSS color
  reducedMotion?: boolean;
  onHover?: (meta: any)=>void;
  onClick?: ()=>void;
  config?: { fresnel?: number; bloom?: number };
  style?: React.CSSProperties;
  onReady?: (api: { snapshot: () => string }) => void;
};

export function CompanySlab(props: CompanySlabProps){
  const width = 420; const height = 120;
  return (
    <div style={{ width: "100%", height: 180, ...props.style }}>
      <Canvas dpr={[1, 1.6]} camera={{ fov: 38, position: [0, 0, 6] }} onCreated={({ gl }) => {
        if (props.onReady){
          props.onReady({ snapshot: () => gl.domElement.toDataURL("image/png") });
        }
      }}>
        <color attach="background" args={["#0A0F16"]} />
        <ambientLight intensity={0.3} />
        <pointLight position={[6,6,6]} intensity={0.8} color={props.healthColor || "#00F0FF"} />
        <SlabMesh {...props} />
        <OrbitControls enablePan={false} enableZoom={false} enableDamping dampingFactor={0.06} />
      </Canvas>
    </div>
  );
}

function SlabMesh({ logoUrl, signalScore = 50, healthColor = "#00F0FF", reducedMotion, onHover, onClick }: CompanySlabProps){
  const group = useRef<THREE.Group>(null);
  const geom = useMemo(() => new THREE.BoxGeometry(3.8, 1.2, 0.1, 16, 16, 2), []);
  const mat = useMemo(() => new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(0x0b1220), transmission: 0.6, thickness: 0.25, roughness: 0.34, metalness: 0.1,
    clearcoat: 0.6, clearcoatRoughness: 0.4, reflectivity: 0.5,
  }), []);
  const ringGeom = useMemo(()=> new THREE.RingGeometry(0.7, 0.75, 64), []);
  const ringMat = useMemo(()=> new THREE.MeshBasicMaterial({ color: healthColor, transparent: true, opacity: 0.85 }), [healthColor]);
  const logoMat = useMemo(()=> new THREE.MeshBasicMaterial({ color: "white" }), []);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (group.current){
      const breathe = reducedMotion ? 0 : (Math.sin(t * 0.6) * 0.006);
      group.current.scale.setScalar(1 + breathe);
      const rx = reducedMotion ? 0 : Math.sin(t * 0.2) * 0.03;
      const ry = reducedMotion ? 0 : Math.cos(t * 0.16) * 0.03;
      group.current.rotation.set(rx, ry, 0);
    }
  });

  return (
    <group ref={group} onPointerOver={()=> onHover?.({ signalScore })} onClick={onClick}>
      <mesh geometry={geom} material={mat} />
      <mesh geometry={ringGeom} material={ringMat} position={[-1.6, 0, 0.08]} rotation={[Math.PI/2, 0, 0]} />
      <mesh position={[-1.6, 0, 0.081]}>
        <planeGeometry args={[1.2, 1.2]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
      {/* Signal tick */}
      <mesh position={[-1.6 + ((signalScore/100)*1.4) - 0.7, -0.45, 0.09]}>
        <boxGeometry args={[0.06, 0.06, 0.06]} />
        <meshBasicMaterial color={healthColor} />
      </mesh>
    </group>
  );
}

export default CompanySlab;
