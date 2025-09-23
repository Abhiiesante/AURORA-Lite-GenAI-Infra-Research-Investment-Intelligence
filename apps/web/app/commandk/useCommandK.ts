"use client";
import { useCallback, useMemo, useRef } from "react";
import { useCmdKStore } from "@/app/cmdkStore";

export type CmdKResult = {
  id: string;
  type: string;
  title: string;
  subtitle?: string;
  score?: number;
  actions?: { id: string; label: string }[];
  thumbnail_url?: string;
};

export type CmdKSearchResponse = {
  query: string;
  results: CmdKResult[];
  suggestions?: string[];
  took_ms?: number;
};

type ThumbnailCacheEntry = { url: string; at: number; cacheHit: boolean };

export function useCommandK() {
  const { open, close } = useCmdKStore();
  const lru = useRef(new Map<string, ThumbnailCacheEntry>());
  const maxCache = 64;
  const suggestCache = useRef(new Map<string, { at: number; data: CmdKSearchResponse }>());
  const ttlMs = 20_000; // 20s TTL for suggest cache
  const base = (typeof window !== 'undefined' && (window as any).NEXT_PUBLIC_API_URL) || process.env.NEXT_PUBLIC_API_URL || '';
  const hasUpstream = !!base;

  const openSearch = useCallback((opts?: { initialQuery?: string }) => {
    if (opts?.initialQuery) useCmdKStore.getState().setQuery(opts.initialQuery);
    open();
  }, [open]);

  const closeSearch = useCallback(() => { close(); }, [close]);

  const suggest = useCallback(async (q: string, limit = 12, scope = "global"): Promise<CmdKSearchResponse> => {
    const key = `${q}|${limit}|${scope}`;
    const now = Date.now();
    const cached = suggestCache.current.get(key);
    if (cached && (now - cached.at) < ttlMs) {
      // kick a background refresh
      (async () => {
        try {
          const url = hasUpstream ? `${base.replace(/\/$/, '')}/cmdk/search?q=${encodeURIComponent(q)}&limit=${limit}` : `/api/cmdk/search?q=${encodeURIComponent(q)}&limit=${limit}&scope=${scope}`;
          const res = await fetch(url, { cache: 'no-store' });
          if (res.ok) {
            const fresh = await res.json();
            suggestCache.current.set(key, { at: Date.now(), data: fresh });
          }
        } catch { /* ignore */ }
      })();
      return cached.data;
    }
    const url = hasUpstream ? `${base.replace(/\/$/, '')}/cmdk/search?q=${encodeURIComponent(q)}&limit=${limit}` : `/api/cmdk/search?q=${encodeURIComponent(q)}&limit=${limit}&scope=${scope}`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`search failed: ${res.status}`);
    const data = await res.json();
    suggestCache.current.set(key, { at: now, data });
    return data;
  }, []);

  type ExecHandlers = { onProgress?: (e: { jobId?: string; progress?: number }) => void; onState?: (state: string) => void };
  const execute = useCallback(async (actionId: string, payload: any, handlers?: ExecHandlers) => {
    const url = hasUpstream ? `${base.replace(/\/$/, '')}/cmdk/command` : `/api/cmdk/command`;
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cmd: actionId, payload }) });
    if (!res.ok) throw new Error(`command failed: ${res.status}`);
    const body = await res.json();
    // If upstream, try to attach SSE stream for progress via statusUrl or jobId
    if (hasUpstream && (body?.statusUrl || body?.jobId)) {
      try {
        const streamUrl = body.statusUrl ? (body.statusUrl.startsWith('http') ? body.statusUrl : `${base.replace(/\/$/, '')}${body.statusUrl}`) : `${base.replace(/\/$/, '')}/cmdk/stream?job_id=${encodeURIComponent(body.jobId)}`;
        const es = new EventSource(streamUrl);
        es.onmessage = () => {};
        const onProgress = handlers?.onProgress;
        const onState = handlers?.onState;
        if (onProgress) {
          es.addEventListener('progress', (evt: MessageEvent) => {
            try {
              const data = JSON.parse(String((evt as any).data || '{}'));
              onProgress({ jobId: data.jobId, progress: data.progress });
            } catch {}
          });
        }
        if (onState) {
          es.addEventListener('state', (evt: MessageEvent) => {
            try {
              const data = JSON.parse(String((evt as any).data || '{}'));
              onState(String(data.state || ''));
            } catch {}
          });
        }
        // Close after done and emit final state
        es.addEventListener('done', (evt: MessageEvent) => {
          try {
            if (onState) onState('done');
          } catch {}
          es.close();
        });
      } catch { /* ignore SSE errors */ }
    }
    return body;
  }, []);

  const getThumbnail = useCallback(async (entityId: string, size = "160x96") => {
    const key = `${entityId}|${size}`;
    const now = Date.now();
    if (lru.current.has(key)) {
      const v = lru.current.get(key)!;
      v.at = now;
      return { url: v.url, cacheHit: true };
    }
    const url = hasUpstream ? `${base.replace(/\/$/, '')}/cmdk/thumbnail?entity=${encodeURIComponent(entityId)}&size=${encodeURIComponent(size)}` : `/api/cmdk/render/thumbnail?entity=${encodeURIComponent(entityId)}&size=${encodeURIComponent(size)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`thumb failed: ${res.status}`);
    const data = await res.json();
    const entry = { url: data.pngUrl as string, at: now, cacheHit: !!data.cacheHit };
    lru.current.set(key, entry);
    // LRU eviction
    if (lru.current.size > maxCache) {
      const oldest = [...lru.current.entries()].sort((a,b)=>a[1].at-b[1].at)[0]?.[0];
      if (oldest) lru.current.delete(oldest);
    }
    return { url: entry.url, cacheHit: entry.cacheHit };
  }, []);

  return useMemo(() => ({ openSearch, closeSearch, suggest, execute, getThumbnail }), [openSearch, closeSearch, suggest, execute, getThumbnail]);
}
