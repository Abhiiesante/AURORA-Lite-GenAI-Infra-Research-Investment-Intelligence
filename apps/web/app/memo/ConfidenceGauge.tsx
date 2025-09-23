"use client";
import React, { useRef, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { motion } from "framer-motion";
import * as THREE from "three";

interface ConfidenceGaugeProps {
  confidence: number; // 0-1 scale
  size?: number;
}

// 3D Ring component
function ConfidenceRing({ confidence, size = 120 }: { confidence: number; size: number }) {
  const ringRef = useRef(null);
  const glowRef = useRef(null);

  useFrame((state) => {
    if (!ringRef.current || !glowRef.current) return;
    
    // Gentle rotation
    ringRef.current.rotation.z += 0.005;
    
    // Subtle breathing effect
    const breathe = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.02;
    ringRef.current.scale.setScalar(breathe);
    
    // Glow intensity based on confidence
    const material = glowRef.current.material as THREE.MeshBasicMaterial;
    material.opacity = 0.3 + confidence * 0.4;
  });

  // Get color based on confidence level
  const getConfidenceColor = (conf: number) => {
    if (conf < 0.5) return new THREE.Color('#FF6B6B'); // Low - red
    if (conf < 0.8) return new THREE.Color('#FFB86B'); // Med - amber
    return new THREE.Color('#51CF66'); // High - green
  };

  const confidenceColor = getConfidenceColor(confidence);

  // Create ring geometry with partial sweep based on confidence
  const ringGeometry = new THREE.RingGeometry(0.8, 1.0, 32, 1, 0, Math.PI * 2 * confidence);

  return (
    <group>
      {/* Background ring */}
      <mesh rotation={[0, 0, 0]}>
        <ringGeometry args={[0.8, 1.0, 32]} />
        <meshBasicMaterial 
          color="#1a1a2e" 
          transparent 
          opacity={0.3}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Confidence ring */}
      <mesh ref={ringRef} rotation={[0, 0, -Math.PI / 2]}>
        <primitive object={ringGeometry} />
        <meshBasicMaterial 
          color={confidenceColor}
          transparent 
          opacity={0.8}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Glow effect */}
      <mesh ref={glowRef} rotation={[0, 0, -Math.PI / 2]} scale={1.1}>
        <primitive object={ringGeometry} />
        <meshBasicMaterial 
          color={confidenceColor}
          transparent 
          opacity={0.3}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Inner highlight */}
      <mesh rotation={[0, 0, -Math.PI / 2]} scale={0.95}>
        <primitive object={new THREE.RingGeometry(0.82, 0.84, 32, 1, 0, Math.PI * 2 * confidence)} />
        <meshBasicMaterial 
          color="#ffffff"
          transparent 
          opacity={0.6}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
}

export function ConfidenceGauge({ confidence, size = 120 }: ConfidenceGaugeProps) {
  const percentage = Math.round(confidence * 100);
  
  // Get confidence label and color
  const getConfidenceInfo = (conf: number) => {
    if (conf < 0.5) return { label: 'Low', color: '#FF6B6B' };
    if (conf < 0.8) return { label: 'Medium', color: '#FFB86B' };
    return { label: 'High', color: '#51CF66' };
  };

  const { label, color } = getConfidenceInfo(confidence);

  return (
    <motion.div
      className="confidence-gauge"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 0.84, 0.24, 1] }}
      style={{
        position: 'relative',
        width: size,
        height: size,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      {/* 3D Canvas */}
      <Canvas
        style={{ 
          width: size, 
          height: size,
          position: 'absolute',
          top: 0,
          left: 0
        }}
        camera={{ position: [0, 0, 3], fov: 50 }}
        gl={{ alpha: true, antialias: true }}
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[0, 0, 2]} intensity={0.6} />
        <ConfidenceRing confidence={confidence} size={size} />
      </Canvas>

      {/* Center content */}
      <div
        style={{
          position: 'absolute',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2,
          pointerEvents: 'none'
        }}
      >
        <motion.div
          className="memo-numeric"
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          style={{
            fontSize: Math.max(size * 0.2, 18),
            fontWeight: '600',
            color,
            marginBottom: '2px',
            textShadow: '0 2px 8px rgba(0,0,0,0.3)'
          }}
        >
          {percentage}%
        </motion.div>
        
        <motion.div
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.4 }}
          style={{
            fontSize: Math.max(size * 0.1, 11),
            fontWeight: '500',
            color: 'rgba(230, 238, 252, 0.7)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            textShadow: '0 1px 4px rgba(0,0,0,0.3)'
          }}
        >
          {label}
        </motion.div>
      </div>

      {/* Subtle background glow */}
      <div
        style={{
          position: 'absolute',
          width: size * 1.2,
          height: size * 1.2,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${color}20 0%, transparent 60%)`,
          zIndex: -1
        }}
      />
    </motion.div>
  );
}