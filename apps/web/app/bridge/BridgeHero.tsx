// @ts-nocheck
"use client";
import { Canvas, useThree } from "@react-three/fiber";
import { Suspense, useMemo, useEffect } from "react";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";

export type BridgeHeroProps = {
  nodes: Array<{ id: string; x: number; y: number; z: number; score: number; meta?: any }>;
  clusters: Array<{ id: string; nodes: string[]; label?: string }>;
  onNodeHover?: (id: string, meta?: any) => void;
  onNodeClick?: (id: string) => void;
  onSceneReady?: (api: { animateCameraZ: (z: number) => void }) => void;
  config?: {
    particles?: { near?: number; mid?: number; far?: number };
    bloom?: number;
    fresnelPower?: number;
    particleCount?: number;
    enablePostprocessing?: boolean;
  };
};

function Globe({ fresnelPower = 2.4 }: { fresnelPower?: number }) {
  return (
    <group>
      <mesh>
        <sphereGeometry args={[1.2, 64, 64]} />
        <shaderMaterial
          transparent
          uniforms={{ uTime: { value: 0 }, uFresnel: { value: fresnelPower } }}
          vertexShader={`
            varying vec3 vNormal;
            void main(){
              vNormal = normalize(normalMatrix * normal);
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
            }
          `}
          fragmentShader={`
            varying vec3 vNormal;
            uniform float uFresnel;
            float fresnel(vec3 n, vec3 v, float p){
              return pow(1.0 - max(dot(normalize(n), normalize(v)), 0.0), p);
            }
            void main(){
              vec3 viewDir = vec3(0.,0.,1.);
              float f = fresnel(vNormal, viewDir, uFresnel);
              vec3 rim = mix(vec3(0.,0.,0.), vec3(0.0,1.0,1.0), f);
              gl_FragColor = vec4(rim, 0.35 + 0.4*f);
            }
          `}
        />
      </mesh>
    </group>
  );
}

function OrbitRings() {
  const rings = useMemo(() => [1.6, 2.4, 3.2] as number[], []);
  return (
    <group>
      {rings.map((r: number, i: number) => (
        <mesh key={i} rotation={[Math.PI / 3 * (i+1), 0, 0]}>
          <torusGeometry args={[r, 0.01, 8, 128]} />
          <meshBasicMaterial color={i % 2 ? "#00F0FF" : "#B266FF"} wireframe transparent opacity={0.6} />
        </mesh>
      ))}
    </group>
  );
}

function ParticleField({ count = 8000 }: { count?: number }) {
  const geom = useMemo(() => new THREE.BufferGeometry(), []);
  const pos = useMemo(() => {
    const a = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      a[i * 3 + 0] = (Math.random() - 0.5) * 12;
      a[i * 3 + 1] = (Math.random() - 0.5) * 8;
      a[i * 3 + 2] = (Math.random() - 0.5) * 12;
    }
    return a;
  }, [count]);
  geom.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  return (
    <points>
      <primitive object={geom} attach="geometry" />
      <pointsMaterial size={0.02} sizeAttenuation color="#7CE9FF" transparent opacity={0.5} />
    </points>
  );
}

export default function BridgeHero(props: BridgeHeroProps) {
  const bloom = props.config?.bloom ?? 0.75;
  const fresnel = props.config?.fresnelPower ?? 2.4;
  const particleCount = props.config?.particleCount ?? 8000;
  const enablePP = props.config?.enablePostprocessing ?? true;
  return (
    <div style={{ width: "100%", height: "60vh", minHeight: 640 }}>
      <Canvas dpr={[1, 1.6]} camera={{ fov: 45, position: [0, 0, 6] }}>
        {props.onSceneReady && <SceneAPI onReady={props.onSceneReady} />}
        <color attach="background" args={["#05070A"]} />
        <ambientLight intensity={0.1} />
        <pointLight color="#00F0FF" intensity={0.5} position={[4, 2, 6]} />
        <pointLight color="#B266FF" intensity={0.5} position={[-4, -2, -6]} />
        <Suspense fallback={null}>
          <Globe fresnelPower={fresnel} />
          <OrbitRings />
          <NodesCloud nodes={props.nodes} onHover={props.onNodeHover} onClick={props.onNodeClick} />
          {particleCount > 0 && <ParticleField count={particleCount} />}
        </Suspense>
        {enablePP && bloom > 0 && (
          <EffectComposer>
            <Bloom intensity={bloom} luminanceThreshold={0.2} luminanceSmoothing={0.9} />
          </EffectComposer>
        )}
      </Canvas>
    </div>
  );
}

function SceneAPI({ onReady }: { onReady: (api: { animateCameraZ: (z: number) => void }) => void }){
  const { camera, invalidate } = useThree();
  useEffect(() => {
    const api = {
      animateCameraZ: (z: number) => {
        camera.position.z = z;
        camera.updateProjectionMatrix();
        invalidate();
      },
    };
    onReady(api);
  }, [camera, invalidate, onReady]);
  return null;
}

function NodesCloud({ nodes, onHover, onClick }: { nodes: Array<{ id: string; x: number; y: number; z: number; score: number; meta?: any }>; onHover?: (id: string, meta?: any)=>void; onClick?: (id: string)=>void }){
  const count = Math.min(nodes.length, 800);
  const instRef = useMemo(() => new THREE.InstancedMesh(new THREE.SphereGeometry(0.05, 12, 12), new THREE.MeshBasicMaterial({ vertexColors: true }), count), [count]);
  useEffect(() => {
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    for (let i = 0; i < count; i++) {
      const n = nodes[i];
      const s = 0.03 + (Math.max(0, Math.min(100, n.score)) / 100) * 0.06;
      dummy.position.set(n.x, n.y, n.z);
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      instRef.setMatrixAt(i, dummy.matrix);
      // color blend: score 0 = violet, 100 = cyan
      color.setRGB(
        (178 + (0 - 178) * (n.score / 100)) / 255,
        (102 + (240 - 102) * (n.score / 100)) / 255,
        (255 + (255 - 255) * (n.score / 100)) / 255
      );
      // @ts-ignore
      instRef.setColorAt?.(i, color);
    }
    // @ts-ignore
    instRef.instanceMatrix.needsUpdate = true;
    // @ts-ignore
    if (instRef.instanceColor) instRef.instanceColor.needsUpdate = true;
  }, [nodes, instRef, count]);

  const handleMove = (e: any) => {
    if (e.instanceId == null) return;
    const i = e.instanceId as number;
    const n = nodes[i];
    onHover?.(n.id, n.meta);
  };
  const handleClick = (e: any) => {
    if (e.instanceId == null) return;
    const i = e.instanceId as number;
    onClick?.(nodes[i].id);
  };
  return (
    <primitive object={instRef} onPointerMove={handleMove} onClick={handleClick} />
  );
}
