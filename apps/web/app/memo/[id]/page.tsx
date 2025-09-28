import MemoClient from "./page_client";

export const dynamic = process.env.STATIC_EXPORT ? "auto" : "force-dynamic";

export async function generateStaticParams(){
  if(!process.env.STATIC_EXPORT) return [];
  return [{ id: "sample" }, { id: "demo" }, { id: "1" }];
}

export default function MemoWrapper(props: any){
  return <MemoClient {...props} />;
}