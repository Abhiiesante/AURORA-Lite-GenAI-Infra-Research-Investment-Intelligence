// @ts-nocheck
"use client";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { Suspense, useEffect, useMemo, useRef } from "react";

export type ExplorerNode = {
  id: string;
  name: string;
  x: number; y: number; z: number;
  sector: string;
  signal: number;
  metrics?: any;
};
export type ExplorerEdge = { source: string; target: string; weight: number };

export type ClusterExplorerProps = {
  nodes: ExplorerNode[];
  edges: ExplorerEdge[];
  onNodeHover?: (id: string) => void;
  onNodeClick?: (id: string) => void;
  onReady?: (api: { snapshot: () => string; resetCamera: () => void }) => void;
  reducedMotion?: boolean;
};

const sectorColors: Record<string, THREE.ColorRepresentation> = {
  tech: "#00F0FF",
  healthcare: "#B266FF",
  finance: "#FFB86B",
  energy: "#B2FF66",
  retail: "#66FFD9",
};

export default function ClusterExplorer(props: ClusterExplorerProps){
  const particleCount = props.reducedMotion ? 0 : 3000;
  return (
    <div style={{ width: "100%", height: "70vh", minHeight: 560 }}>
      <Canvas dpr={[1, 1.6]} camera={{ fov: 50, position: [0, 0, 8] }}>
        <SceneBridge onReady={props.onReady} />
        <color attach="background" args={["#05070A"]} />
        <ambientLight intensity={0.2} />
        <pointLight position={[6, 4, 8]} intensity={0.6} color="#00F0FF" />
        <pointLight position={[-6, -4, -8]} intensity={0.4} color="#B266FF" />
        <Suspense fallback={null}>
          <EdgesLines nodes={props.nodes} edges={props.edges} reduced={!!props.reducedMotion} />
          <InstancedNodes nodes={props.nodes} onHover={props.onNodeHover} onClick={props.onNodeClick} reduced={!!props.reducedMotion} />
          {particleCount > 0 && <StarField count={particleCount} />}
        </Suspense>
        <OrbitControls enableDamping dampingFactor={0.08} makeDefault />
      </Canvas>
    </div>
  );
}

function SceneBridge({ onReady }: { onReady?: (api: { snapshot: () => string; resetCamera: () => void }) => void }){
  const { gl, camera, controls } = useThree();
  useEffect(() => {
    if (!onReady) return;
    const api = {
      snapshot: () => gl.domElement.toDataURL("image/png"),
      resetCamera: () => {
        camera.position.set(0, 0, 8);
        camera.lookAt(0, 0, 0);
        // @ts-ignore
        controls?.reset?.();
      },
    };
    onReady(api);
  }, [onReady, gl, camera, controls]);
  return null;
}

function InstancedNodes({ nodes, onHover, onClick, reduced }: { nodes: ExplorerNode[]; onHover?: (id: string)=>void; onClick?: (id: string)=>void; reduced: boolean }){
  const count = Math.min(nodes.length, 1500);
  const geom = useMemo(() => new THREE.SphereGeometry(0.06, reduced ? 8 : 16, reduced ? 8 : 16), [reduced]);
  const mat = useMemo(() => new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.95 }), []);
  const meshRef = useRef<any>();
  useEffect(() => {
    if (!meshRef.current) meshRef.current = new THREE.InstancedMesh(geom, mat, count);
    const inst = meshRef.current as THREE.InstancedMesh;
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    for (let i = 0; i < count; i++) {
      const n = nodes[i];
      const size = 0.04 + (Math.max(0, Math.min(100, n.signal)) / 100) * 0.09;
      dummy.position.set(n.x, n.y, n.z);
      dummy.scale.setScalar(size);
      dummy.updateMatrix();
      inst.setMatrixAt(i, dummy.matrix);
      color.set(sectorColors[n.sector] || "#7CE9FF");
      // @ts-ignore
      inst.setColorAt?.(i, color);
    }
    // @ts-ignore
    inst.instanceMatrix.needsUpdate = true;
    // @ts-ignore
    if (inst.instanceColor) inst.instanceColor.needsUpdate = true;
  }, [nodes, count, geom, mat]);

  const handleMove = (e: any) => {
    if (e.instanceId == null) return;
    onHover?.(nodes[e.instanceId].id);
  };
  const handleClick = (e: any) => {
    if (e.instanceId == null) return;
    onClick?.(nodes[e.instanceId].id);
  };
  return <primitive object={meshRef.current} onPointerMove={handleMove} onClick={handleClick} />;
}

function EdgesLines({ nodes, edges, reduced }: { nodes: ExplorerNode[]; edges: ExplorerEdge[]; reduced: boolean }){
  const posAttr = useMemo(() => {
    const positions = new Float32Array(edges.length * 2 * 3);
    const indexById = new Map(nodes.map((n, i) => [n.id, i] as const));
    let p = 0;
    for (const e of edges) {
      const si = indexById.get(e.source); const ti = indexById.get(e.target);
      if (si == null || ti == null) continue;
      const s = nodes[si]; const t = nodes[ti];
      positions[p++] = s.x; positions[p++] = s.y; positions[p++] = s.z;
      positions[p++] = t.x; positions[p++] = t.y; positions[p++] = t.z;
    }
    return new THREE.BufferAttribute(positions, 3);
  }, [nodes, edges]);
  const geom = useMemo(() => new THREE.BufferGeometry(), []);
  geom.setAttribute("position", posAttr);
  return (
    <lineSegments>
      <primitive object={geom} attach="geometry" />
      <lineBasicMaterial color={reduced ? "#7CE9FF" : "#B266FF"} transparent opacity={reduced ? 0.2 : 0.45} />
    </lineSegments>
  );
}

function StarField({ count = 3000 }: { count?: number }){
  const geom = useMemo(() => new THREE.BufferGeometry(), []);
  const pos = useMemo(() => {
    const a = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      a[i*3+0] = (Math.random() - 0.5) * 40;
      a[i*3+1] = (Math.random() - 0.5) * 24;
      a[i*3+2] = (Math.random() - 0.5) * 40;
    }
    return a;
  }, [count]);
  geom.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  useFrame(({ clock, scene }) => {
    const t = clock.getElapsedTime();
    // gentle parallax hue shift on background
    scene.fog = undefined;
  });
  return (
    <points>
      <primitive object={geom} attach="geometry" />
      <pointsMaterial size={0.02} color="#7CE9FF" sizeAttenuation transparent opacity={0.45} />
    </points>
  );
}
