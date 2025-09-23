"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchWithETag } from "../providers";

const etagCache = new Map<string, any>();

export function useKPIs(){
  return useQuery({
    queryKey: ["kpis"],
    queryFn: async () => await fetchWithETag("/api/kpis", { etagCache })
  });
}

export function useNodes(){
  return useQuery({
    queryKey: ["nodes"],
    queryFn: async () => await fetchWithETag("/api/nodes", { etagCache })
  });
}
