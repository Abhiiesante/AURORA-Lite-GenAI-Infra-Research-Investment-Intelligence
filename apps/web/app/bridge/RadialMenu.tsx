"use client";
import { useEffect, useRef } from "react";

type Item = { id: string; label: string; onSelect?: () => void };

export default function RadialMenu({ open, onClose, items = [] }: { open: boolean; onClose: () => void; items?: Item[] }) {
  const dialogRef = useRef(null as unknown as HTMLDivElement | null);

  useEffect(() => {
    if (!open) return;
    const prevActive = document.activeElement as HTMLElement | null;
    const firstBtn = dialogRef.current?.querySelector("button") as HTMLButtonElement | null;
    firstBtn?.focus();
    function onKey(e: KeyboardEvent){
      if (e.key === "Escape") { e.preventDefault(); onClose(); }
    }
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); prevActive?.focus(); };
  }, [open, onClose]);

  if (!open) return null;

  const radius = 96;
  const centerStyle: React.CSSProperties = { position: "fixed", right: 52, bottom: 52 };
  return (
    <div role="dialog" aria-modal="true" aria-label="Command menu" ref={dialogRef} style={{ position: "fixed", inset: 0 }}>
      <button aria-label="Close" onClick={onClose} style={{ position: "fixed", inset: 0, background: "transparent", border: "none" }} />
      <div style={centerStyle}>
        {items.map((it, idx) => {
          const angle = (Math.PI * 2 * idx) / items.length - Math.PI / 2;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;
          return (
            <button
              key={it.id}
              onClick={() => { it.onSelect?.(); onClose(); }}
              style={{ position: "absolute", transform: `translate(${x}px, ${y}px)`,
                width: 44, height: 44, borderRadius: 999, border: "1px solid rgba(255,255,255,0.2)", color: "var(--starlight)",
                background: "rgba(5,7,10,0.7)", backdropFilter: "blur(6px)" }}
            >{it.label}</button>
          );
        })}
      </div>
    </div>
  );
}
