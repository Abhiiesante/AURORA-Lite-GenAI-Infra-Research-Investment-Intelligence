"use client";
import { motion } from "framer-motion";

export type KPITileProps = {
  label: string;
  value: string | number;
  deltaPercent?: number;
  trendSeries?: number[];
  status?: "ok" | "warn" | "alert";
  onClick?: () => void;
};

const variants = {
  rest: { translateZ: 0, scale: 1, boxShadow: "0 6px 18px rgba(0,0,0,0.35)" },
  hover: { translateZ: 16, scale: 1.02, transition: { duration: 0.16, ease: [0.2, 0.9, 0.3, 1] } },
  press: { translateZ: 8, transition: { duration: 0.12 } },
};

export default function KPITile({ label, value, deltaPercent, status = "ok", onClick }: KPITileProps) {
  const delta = typeof deltaPercent === "number" ? `${deltaPercent > 0 ? "+" : ""}${deltaPercent.toFixed(1)}%` : undefined;
  const chipColor = status === "alert" ? "var(--solar-alert)" : status === "warn" ? "var(--solar-amber)" : "var(--aurora-cyan)";
  return (
    <motion.button
      initial="rest"
      whileHover="hover"
      whileTap="press"
      variants={variants}
      onClick={onClick}
      aria-label={`${label} ${value}${delta ? `, ${delta}` : ""}`}
      style={{
        width: 320, height: 160,
        backdropFilter: `blur(var(--glass-blur))`, WebkitBackdropFilter: `blur(var(--glass-blur))`,
        background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 16,
        color: "var(--starlight)", display: "flex", flexDirection: "column", justifyContent: "space-between",
        padding: 16,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, opacity: 0.9 }}>
        <span>{label}</span>
        <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 999, background: chipColor, color: "#05070A", fontWeight: 600, fontSize: 11 }}>
          {status}
        </span>
      </div>
      <div style={{ fontFamily: "'Space Grotesk', 'Roboto Mono', monospace", fontSize: 40, lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: 12, opacity: 0.85 }}>{delta ?? ""}</div>
    </motion.button>
  );
}
