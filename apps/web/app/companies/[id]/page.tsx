import CompanyClient from "./page_client";

export async function generateStaticParams(){
  if (!process.env.STATIC_EXPORT) return [];
  return ["sample"].map(id => ({ id }));
}

export const dynamic = process.env.STATIC_EXPORT ? "auto" : "force-dynamic";

// Render client component directly; avoid passing searchParams/params to prevent serialization during static export.
export default function CompanyDetailsWrapper(){
  return <CompanyClient />;
}
