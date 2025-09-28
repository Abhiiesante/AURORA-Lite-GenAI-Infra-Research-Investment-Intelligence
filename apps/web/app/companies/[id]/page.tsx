import CompanyClient from "./page_client";

export async function generateStaticParams(){
  if (!process.env.STATIC_EXPORT) return [];
  // Provide small seed list for static export; real IDs resolved dynamically at runtime otherwise.
  return ["1","sample","demo"].map(id => ({ id }));
}

export const dynamic = process.env.STATIC_EXPORT ? "auto" : "force-dynamic";

export default function CompanyDetailsWrapper(props: any){
  return <CompanyClient {...props} />;
}
