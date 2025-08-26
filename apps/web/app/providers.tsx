"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

type Props = { children?: any };

export default function Providers({ children }: Props) {
  const [client] = useState(() => new QueryClient());
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

// ETag-aware fetch util (client)
export async function fetchWithETag(url: string, init?: RequestInit & { etagCache?: Map<string, any> }) {
  const cache = init?.etagCache;
  const headers: any = { ...(init?.headers || {}) };
  const prev = cache?.get(url);
  if (prev?.etag) headers['If-None-Match'] = prev.etag;
  const res = await fetch(url, { ...init, headers });
  if (res.status === 304 && prev) return prev.data;
  const etag = res.headers.get('ETag') || undefined;
  const data = await res.json();
  if (cache && etag) cache.set(url, { etag, data });
  return data;
}
