"use client";
export default function FAB({ onClick }: { onClick?: () => void }){
  return (
    <button
      aria-label="Command"
      onClick={onClick}
      style={{ position: "fixed", right: 24, bottom: 24, width: 56, height: 56, borderRadius: 999,
        background: "linear-gradient(135deg, var(--aurora-cyan), var(--nebula-violet))", color: "#05070A",
        boxShadow: "0 8px 24px rgba(0,0,0,0.45)", border: "none", fontWeight: 700 }}
    >
      ⊕
    </button>
  );
}
