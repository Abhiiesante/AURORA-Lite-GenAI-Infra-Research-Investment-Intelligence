"use client";
import { useEffect } from "react";

export default function GlobalHotkeys() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isCmdK = (e.ctrlKey || e.metaKey) && (e.key?.toLowerCase?.() === "k");
      if (isCmdK) {
        e.preventDefault();
        window.location.href = "/palette";
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  return null;
}
