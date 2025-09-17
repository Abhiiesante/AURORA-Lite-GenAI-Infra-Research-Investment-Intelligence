"use client";
import { useEffect } from "react";
import { useCmdKStore } from "./cmdkStore";

export default function GlobalHotkeys() {
  const toggle = useCmdKStore((s) => s.toggle);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isCmdK = (e.ctrlKey || e.metaKey) && (e.key?.toLowerCase?.() === "k");
      if (isCmdK) {
        e.preventDefault();
        toggle();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  return null;
}
