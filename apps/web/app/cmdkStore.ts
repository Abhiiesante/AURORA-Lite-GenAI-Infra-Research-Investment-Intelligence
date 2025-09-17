"use client";
import { create } from "zustand";

type CmdKState = {
  isOpen: boolean;
  query: string;
  open: () => void;
  close: () => void;
  toggle: () => void;
  setQuery: (q: string) => void;
};

export const useCmdKStore = create<CmdKState>((set) => ({
  isOpen: false,
  query: "",
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false, query: "" }),
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  setQuery: (q) => set({ query: q }),
}));
