"use client";
import { create } from "zustand";

type SfxState = {
  enabled: boolean;
  volume: number; // 0..1
  toggle: () => void;
  setVolume: (v: number) => void;
};

const getDefaultEnabled = () => {
  if (typeof window === "undefined") return true;
  const pref = localStorage.getItem("aurora_sfx_enabled");
  if (pref !== null) return pref === "1";
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  return !reduced; // disable by default if reduced motion is on
};

export const useSfxStore = create<SfxState>((set, get) => ({
  enabled: getDefaultEnabled(),
  volume: 0.5,
  toggle: () => set((s) => {
    const next = !s.enabled; if (typeof window !== 'undefined') localStorage.setItem('aurora_sfx_enabled', next ? '1':'0'); return { enabled: next };
  }),
  setVolume: (v) => set({ volume: Math.min(1, Math.max(0, v)) }),
}));
