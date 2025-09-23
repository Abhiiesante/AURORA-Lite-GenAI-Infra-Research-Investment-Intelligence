"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchWithETag } from "../providers";

export type ExplorerFilters = { sector?: string[]; stage?: string[]; region?: string[]; seed?: number; count?: number };

const etagCache = new Map<string, any>();

export function useExplorerData(filters: ExplorerFilters = {}){
  const params = new URLSearchParams();
  if (filters.seed != null) params.set("seed", String(filters.seed));
  if (filters.count != null) params.set("count", String(filters.count));
  // sector/stage/region are placeholders for later server-side filtering
  const url = "/api/explorer" + (params.toString() ? `?${params.toString()}` : "");
  return useQuery({
    queryKey: ["explorer", filters],
    queryFn: async () => await fetchWithETag(url, { etagCache })
  });
}
