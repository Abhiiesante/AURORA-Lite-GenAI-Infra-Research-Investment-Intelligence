"use client";
import { useEffect } from "react";
import { useCmdKStore } from "./cmdkStore";

export default function GlobalHotkeys() {
  const toggle = useCmdKStore((s) => s.toggle);
  const open = useCmdKStore((s) => s.open);
  const setQuery = useCmdKStore((s) => s.setQuery);
  useEffect(() => {
    // Initialize reduced motion class from persisted preference
    try {
      const pref = localStorage.getItem('aurora_reduce_motion');
      if (pref === '1') {
        document.documentElement.classList.add('reduce-motion');
      }
    } catch {}

    const handler = (e: KeyboardEvent) => {
      const isCmdK = (e.ctrlKey || e.metaKey) && (e.key?.toLowerCase?.() === "k");
      if (isCmdK) {
        e.preventDefault();
        toggle();
        return;
      }
      // ignore when typing in inputs, textareas or contenteditable
      const t = e.target as HTMLElement | null;
      const isFormField = !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
      if (isFormField) return;
      if (e.key === '/') {
        e.preventDefault();
        setQuery('');
        open();
        return;
      }
      if (e.key === '?') {
        e.preventDefault();
        setQuery('help: shortcuts — ⌘K / Ctrl+K · / search · Esc close');
        open();
      }
    };
    window.addEventListener("keydown", handler);
    const onStorage = (ev: StorageEvent) => {
      if (ev.key === 'aurora_reduce_motion') {
        const on = ev.newValue === '1';
        document.documentElement.classList.toggle('reduce-motion', !!on);
      }
    };
    window.addEventListener('storage', onStorage);
    return () => { window.removeEventListener("keydown", handler); window.removeEventListener('storage', onStorage); };
  }, []);
  return null;
}
