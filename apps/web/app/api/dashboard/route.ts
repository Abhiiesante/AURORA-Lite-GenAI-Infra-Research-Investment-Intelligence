const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const revalidate = 86400; // ISR: 24h

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  const window = searchParams.get("window") || "90d";
  if (!id) return new Response(JSON.stringify({ error: "missing id" }), { status: 400 });
  const upstream = `${api}/company/${id}/dashboard?window=${encodeURIComponent(window)}`;
  const inm = req.headers.get("if-none-match");
  const res = await fetch(upstream, { headers: inm ? { "If-None-Match": inm } : undefined, cache: "no-store" });
  if (res.status === 304) return new Response(null, { status: 304 });
  const etag = res.headers.get("ETag") || undefined;
  const body = await res.text();
  const headers = new Headers({ "Content-Type": "application/json" });
  if (etag) headers.set("ETag", etag);
  return new Response(body, { status: res.status, headers });
}
