"use client";
import { create } from "zustand";

type HeroMotionState = {
  progress: number; // 0..1 scroll progress through pinned hero
  setProgress: (p: number) => void;
};

export const useHeroStore = create<HeroMotionState>((set) => ({
  progress: 0,
  setProgress: (p) => set({ progress: Math.max(0, Math.min(1, p)) }),
}));
