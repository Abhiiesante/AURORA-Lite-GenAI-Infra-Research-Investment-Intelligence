"use client";
import { create } from "zustand";

export type ClusterId = string | null;

type LinkedState = {
  selected: ClusterId;
  hover: ClusterId;
  setSelected: (id: ClusterId) => void;
  setHover: (id: ClusterId) => void;
  clear: () => void;
};

export const useLinkedStore = create<LinkedState>((set) => ({
  selected: null,
  hover: null,
  setSelected: (id) => set({ selected: id }),
  setHover: (id) => set({ hover: id }),
  clear: () => set({ selected: null, hover: null }),
}));
