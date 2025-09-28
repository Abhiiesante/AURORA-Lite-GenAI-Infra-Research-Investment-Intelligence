export const dynamic = process.env.STATIC_EXPORT ? 'auto' : 'force-dynamic';
import dynamicImport from 'next/dynamic';
const MarketMapClient = dynamicImport(() => import('./page_client').then(m => m.default), { ssr: false, loading: () => <div style={{ padding: 24 }}>Loading market map…</div> });

export default function MarketMapPage() {
  return <MarketMapClient />;
}
