"use client";
// Lightweight data layer for Trends page: REST wrappers and a resilient WS hook
import { useEffect, useRef } from "react";

export type Topic = { topic_id: string; label: string; momentum: number; trend_state: 'rising'|'stable'|'declining' };

export function getBaseUrl(){
  // Prefer NEXT_PUBLIC_API_URL for real FastAPI, else use Next.js API routes
  return process.env.NEXT_PUBLIC_API_URL || '';
}

export async function fetchTopics(params: { window?: string } = {}): Promise<{ topics: Topic[] }>{
  const base = getBaseUrl();
  const search = new URLSearchParams();
  if (params.window) search.set('window', params.window);
  const res = await fetch(`${base}/api/topics${search.toString()?`?${search.toString()}`:''}`);
  if (!res.ok) throw new Error(`Failed to load topics: ${res.status}`);
  return res.json();
}

export async function fetchSeries(topicId: string): Promise<{ series: Array<{ date: string; value: number }> }>{
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/topics/${encodeURIComponent(topicId)}/series`);
  if (!res.ok) throw new Error(`Failed to load series: ${res.status}`);
  return res.json();
}

export async function fetchChangePoints(topicId: string): Promise<{ change_points: Array<{ date: string; type: string }> }>{
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/topics/${encodeURIComponent(topicId)}/change_points`);
  if (!res.ok) throw new Error(`Failed to load change points: ${res.status}`);
  return res.json();
}

export async function fetchDrivers(topicId: string){
  const base = getBaseUrl();
  const res = await fetch(`${base}/api/topics/${encodeURIComponent(topicId)}/drivers`);
  if (!res.ok) throw new Error(`Failed to load drivers: ${res.status}`);
  return res.json();
}

export type TopicStreamEvent = { type: string; topic_id?: string; date?: string; [key: string]: any };

// Resilient WebSocket hook with auto-reconnect and simple backoff. No-op if URL unavailable.
export function useTopicStream(options: { url?: string; onEvent?: (e: TopicStreamEvent)=>void; enabled?: boolean }){
  const { url: inputUrl, onEvent, enabled } = options;
  const wsRef = useRef(null as unknown as WebSocket | null);
  const timer = useRef(null as unknown as ReturnType<typeof setTimeout> | null);
  const backoff = useRef(500);

  useEffect(()=>{
    if (!enabled) return;
    const base = getBaseUrl();
    // Default WS endpoint guess; users can override via options.url
    const http = inputUrl || (base ? `${base}/ws/topics` : "");
    if (!http) return;
    let wsUrl = http.replace(/^http/i, 'ws');
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      try {
        wsRef.current = new WebSocket(wsUrl);
      } catch (_e){
        // schedule retry
        timer.current = setTimeout(connect, backoff.current);
        backoff.current = Math.min(backoff.current * 1.6, 5000);
        return;
      }
      backoff.current = 500;
      wsRef.current.onopen = () => {
        backoff.current = 500;
      };
      wsRef.current.onmessage = (msg: MessageEvent) => {
        try {
          const data = JSON.parse(msg.data);
          onEvent?.(data);
        } catch {
          // ignore non-JSON
        }
      };
      wsRef.current.onclose = () => {
        if (!cancelled){
          timer.current = setTimeout(connect, backoff.current);
          backoff.current = Math.min(backoff.current * 1.6, 5000);
        }
      };
      wsRef.current.onerror = () => {
        try { wsRef.current?.close(); } catch {}
      };
    };

    connect();
    return () => {
      cancelled = true;
      if (timer.current) clearTimeout(timer.current);
      try { wsRef.current?.close(); } catch {}
      wsRef.current = null;
    };
  }, [inputUrl, onEvent, enabled]);
}
