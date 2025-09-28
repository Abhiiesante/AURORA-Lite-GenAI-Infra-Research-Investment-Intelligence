import DossierClient from "./page_client";

export async function generateStaticParams(){
  if (!process.env.STATIC_EXPORT) return [];
  return ["sample", "demo", "1"].map(id => ({ id }));
}

export const dynamic = process.env.STATIC_EXPORT ? "auto" : "force-dynamic";

export default function DossierPageWrapper(props: any){
  return <DossierClient {...props} />;
}

