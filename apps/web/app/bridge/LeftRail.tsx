"use client";
import { motion } from "framer-motion";

type Action = {
  id: string;
  label: string;
  ariaLabel?: string;
  onClick?: () => void;
  badge?: string;
};

const baseStyle: React.CSSProperties = {
  width: 80,
  height: 160,
  padding: 12,
  borderRadius: 16,
  backdropFilter: "blur(var(--glass-blur))",
  WebkitBackdropFilter: "blur(var(--glass-blur))",
  background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.12)",
  color: "var(--starlight)",
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  justifyContent: "space-between",
  textAlign: "left",
};

const variants = {
  rest: { width: 80, boxShadow: "0 6px 18px rgba(0,0,0,0.35)" },
  hover: { width: 160, transition: { duration: 0.16, ease: [0.2, 0.9, 0.3, 1] } },
  press: { width: 150, transition: { duration: 0.12 } },
};

export default function LeftRail({ actions }: { actions: Action[] }) {
  return (
    <nav aria-label="Quick actions" style={{ position: "fixed", top: 96, left: 16, display: "flex", flexDirection: "column", gap: 16 }}>
      {actions.map((a) => (
        <motion.button
          key={a.id}
          initial="rest"
          whileHover="hover"
          whileFocus="hover"
          whileTap="press"
          variants={variants}
          onClick={a.onClick}
          aria-label={a.ariaLabel ?? a.label}
          style={baseStyle}
        >
          <span style={{ fontWeight: 700, fontSize: 14 }}>{a.label}</span>
          {a.badge && (
            <span style={{ fontSize: 11, opacity: 0.85, border: "1px solid rgba(255,255,255,0.2)", padding: "2px 6px", borderRadius: 999 }}>{a.badge}</span>
          )}
        </motion.button>
      ))}
    </nav>
  );
}
