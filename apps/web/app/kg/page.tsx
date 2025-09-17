"use client";
export const dynamic = "force-dynamic";
import React, { useMemo, useState } from "react";
import axios from "axios";

const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type QueryResult = { nodes?: any[]; edges?: any[]; as_of?: string };
type NodeView = { node?: any; neighbors?: any[]; edges?: any[]; as_of?: string };
type FindResult = { nodes?: any[]; next_offset?: number | null; next_cursor?: string | null; as_of?: string };

export default function KGExplorer() {
  const [asOf, setAsOf] = useState(new Date().toISOString());
  const [nodeId, setNodeId] = useState("n:alpha");
  const [depth, setDepth] = useState(1 as any);
  const [limit, setLimit] = useState(200 as any);
  const [devToken, setDevToken] = useState("");
  const [queryRes, setQueryRes] = useState(null as any);
  const [nodeRes, setNodeRes] = useState(null as any);
  const [findRes, setFindRes] = useState(null as any);
  const [findType, setFindType] = useState("");
  const [findPrefix, setFindPrefix] = useState("");
  const [findText, setFindText] = useState("");
  const [findCursor, setFindCursor] = useState("");
  const [loading, setLoading] = useState(null as any);

  const query = async () => {
    setLoading("query");
    try {
      const params = new URLSearchParams();
      if (asOf) params.set("at", asOf);
      if (nodeId) params.set("node", nodeId);
      params.set("limit", String(limit));
      const { data } = await axios.get(`${api}/kg/query?${params.toString()}`);
      setQueryRes(data);
    } catch (e) {
      setQueryRes({ nodes: [], edges: [], as_of: asOf });
    } finally {
      setLoading(null);
    }
  };

  const viewNode = async () => {
    if (!nodeId) return;
    setLoading("node");
    try {
      const params = new URLSearchParams();
      if (asOf) params.set("as_of", asOf);
      params.set("depth", String(depth));
      params.set("limit", String(limit));
      const { data } = await axios.get(`${api}/kg/node/${encodeURIComponent(nodeId)}?${params.toString()}`);
      setNodeRes(data);
    } catch (e) {
      setNodeRes({ node: null, neighbors: [], edges: [], as_of: asOf });
    } finally {
      setLoading(null);
    }
  };

  const find = async (cursor?: string) => {
    setLoading("find");
    try {
      const params = new URLSearchParams();
      if (asOf) params.set("as_of", asOf);
      if (findType) params.set("type", findType);
      if (findPrefix) params.set("uid_prefix", findPrefix);
      if (findText) {
        params.set("prop_contains", findText);
      }
      params.set("limit", String(50));
      if (cursor) params.set("cursor", cursor);
      const { data } = await axios.get(`${api}/kg/find?${params.toString()}`);
      setFindRes(data);
      if (data?.next_cursor) setFindCursor(String(data.next_cursor));
    } catch (e) {
      setFindRes({ nodes: [], next_cursor: null, next_offset: null, as_of: asOf });
    } finally {
      setLoading(null);
    }
  };

  const seedSample = async () => {
    if (!devToken) {
      alert("Enter DEV_ADMIN_TOKEN to seed.");
      return;
    }
    setLoading("seed");
    try {
      const headers = { "x-dev-token": devToken } as any;
      // two nodes and one edge
      await axios.post(
        `${api}/admin/kg/nodes/upsert`,
        { uid: "n:alpha", type: "Company", props: { name: "Alpha Inc" } },
        { headers }
      );
      await axios.post(
        `${api}/admin/kg/nodes/upsert`,
        { uid: "n:beta", type: "Company", props: { name: "Beta LLC" } },
        { headers }
      );
      await axios.post(
        `${api}/admin/kg/edges/upsert`,
        { src_uid: "n:alpha", dst_uid: "n:beta", type: "partner_of", props: { since: 2024 } },
        { headers }
      );
      alert("Seeded sample KG: n:alpha —partner_of→ n:beta");
    } catch (e) {
      console.error(e);
      alert("Seed failed. Check token and API.");
    } finally {
      setLoading(null);
    }
  };

  const neighborsCount = useMemo(() => (nodeRes?.neighbors?.length || 0), [nodeRes]);
  const edgesCount = useMemo(() => (nodeRes?.edges?.length || 0), [nodeRes]);

  return (
    <main style={{ padding: 24 }}>
      <h1>KG Explorer</h1>
      <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div>
          <h3>Dev: Admin Token</h3>
          <input
            value={devToken}
            onChange={(e:any)=>setDevToken(e.target.value)}
            placeholder="DEV_ADMIN_TOKEN (for seeding)"
            style={{ width: '100%' }}
          />
          <small>Token is sent via x-dev-token header for local admin endpoints.</small>
        </div>
        <div style={{ display: 'flex', alignItems: 'end', gap: 8 }}>
          <button onClick={seedSample} disabled={loading==='seed'}>
            {loading==='seed' ? 'Seeding…' : 'Seed sample KG'}
          </button>
        </div>
      </section>
      <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div>
          <h3>Time</h3>
          <input value={asOf} onChange={(e:any)=>setAsOf(e.target.value)} style={{ width: '100%' }} />
          <small>ISO time; leave as now to view latest</small>
        </div>
        <div>
          <h3>Node</h3>
          <input value={nodeId} onChange={(e:any)=>setNodeId(e.target.value)} placeholder="uid (e.g., n:alpha)" style={{ width: '100%' }} />
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <input type="number" value={depth} onChange={(e:any)=>setDepth(Number(e.target.value)||0)} style={{ width: 120 }} />
            <input type="number" value={limit} onChange={(e:any)=>setLimit(Number(e.target.value)||1)} style={{ width: 160 }} />
            <button onClick={viewNode} disabled={loading==='node'}>{loading==='node' ? 'Loading…' : 'View Node'}</button>
          </div>
          {nodeRes && (
            <div style={{ marginTop: 8 }}>
              <div><strong>Node:</strong> {nodeRes.node?.uid} ({nodeRes.node?.type})</div>
              <div><strong>Neighbors:</strong> {neighborsCount} | <strong>Edges:</strong> {edgesCount}</div>
              <details style={{ marginTop: 8 }}>
                <summary>Neighbors JSON</summary>
                <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(nodeRes.neighbors, null, 2)}</pre>
              </details>
              <details>
                <summary>Edges JSON</summary>
                <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(nodeRes.edges, null, 2)}</pre>
              </details>
            </div>
          )}
        </div>
      </section>

      <section style={{ marginTop: 24 }}>
        <h3>Query</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button onClick={query} disabled={loading==='query'}>{loading==='query' ? 'Loading…' : 'Run /kg/query'}</button>
        </div>
        {queryRes && (
          <div style={{ marginTop: 8 }}>
            <div><strong>Nodes:</strong> {queryRes.nodes?.length || 0} | <strong>Edges:</strong> {queryRes.edges?.length || 0}</div>
            <details style={{ marginTop: 8 }}>
              <summary>Result JSON</summary>
              <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(queryRes, null, 2)}</pre>
            </details>
          </div>
        )}
      </section>

      <section style={{ marginTop: 24 }}>
        <h3>Find</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input value={findType} onChange={(e:any)=>setFindType(e.target.value)} placeholder="type (optional)" />
          <input value={findPrefix} onChange={(e:any)=>setFindPrefix(e.target.value)} placeholder="uid prefix (optional)" />
          <input value={findText} onChange={(e:any)=>setFindText(e.target.value)} placeholder="prop contains (optional)" />
          <button onClick={()=>find()} disabled={loading==='find'}>{loading==='find' ? 'Loading…' : 'Run /kg/find'}</button>
          {findRes?.next_cursor && (
            <button onClick={()=>find(findRes.next_cursor||undefined)}>Next Page</button>
          )}
        </div>
        {findRes && (
          <div style={{ marginTop: 8 }}>
            <div><strong>Nodes:</strong> {findRes.nodes?.length || 0}</div>
            <details style={{ marginTop: 8 }}>
              <summary>Result JSON</summary>
              <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(findRes, null, 2)}</pre>
            </details>
          </div>
        )}
      </section>
    </main>
  );
}
