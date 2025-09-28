import { NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(_req: Request, { params }: { params: { id: string }}){
  const id = params.id;
  
  try {
    // Fetch company data from FastAPI endpoints
    const [dashboardRes, insightsRes, signalRes] = await Promise.all([
      fetch(`${API_BASE}/company/${id}/dashboard`).then(r => r.ok ? r.json() : null),
      fetch(`${API_BASE}/insights/company/${id}`).then(r => r.ok ? r.json() : null),
      fetch(`${API_BASE}/signal/${id}`).then(r => r.ok ? r.json() : null)
    ]);

    // Derive company name from insights or dashboard
    const companyName = insightsRes?.company || dashboardRes?.company || (id[0]?.toUpperCase() + id.slice(1)) || "Unknown";
    const thesis = insightsRes?.summary || "AI-powered growth analysis";
    
    // Extract signal score from sparklines or default
    const sparklines = dashboardRes?.sparklines || [];
    const signalSparkline = sparklines.find((s: any) => s.metric?.includes('signal'));
    const signalScore = signalSparkline?.values?.[signalSparkline.values.length - 1]?.value || 
                       Math.floor(Math.random() * 40) + 60; // Fallback 60-100

    // Transform signal series data for metrics
    const signalSeries = signalRes?.series || [];
    const transformMetrics = (metricName: string) => {
      return signalSeries
        .filter((item: any) => item.metric === metricName)
        .map((item: any) => ({ date: item.date, value: item.value }))
        .slice(0, 10); // Limit for performance
    };

    const company = {
      id: `company:${id}`,
      name: companyName,
      slug: id,
      logo: `https://dummyimage.com/256x256/0af/fff.png&text=${encodeURIComponent(companyName[0]?.toUpperCase() || 'C')}`,
      thesis,
      signalScore: Math.round(signalScore),
      metrics: {
        revenue: transformMetrics('revenue_mentions') || [
          { date: "2024-01-01", value: 2.1 },
          { date: "2024-04-01", value: 2.6 },
          { date: "2024-07-01", value: 3.3 },
        ],
        commits: transformMetrics('github_commits') || [
          { date: "2024-01-01", value: 120 },
          { date: "2024-02-01", value: 90 },
          { date: "2024-03-01", value: 140 },
        ],
        jobs: transformMetrics('job_postings') || [
          { date: "2024-01-01", value: 12 },
          { date: "2024-02-01", value: 16 },
          { date: "2024-03-01", value: 14 },
        ]
      },
      repos: dashboardRes?.sources?.filter((s: any) => s.url?.includes('github.com'))?.slice(0, 3)?.map((s: any) => ({
        url: s.url,
        stars: Math.floor(Math.random() * 5000) + 100 // Placeholder
      })) || [{ url: "https://github.com/example/example", stars: 1234 }],
      timeline: [
        { id: "evt1", type: "funding", date: "2024-06-12", title: "Series B $60M", sources: [{ doc_id: "doc:press-2024", url: "https://techcrunch.com/..." }]},
        { id: "evt2", type: "hiring", date: "2024-07-05", title: "Key ML hires", sources: [{ doc_id: "doc:linkedin-2024", url: "https://www.linkedin.com/..." }]},
      ]
    };
    
    return NextResponse.json(company, { 
      headers: { "Cache-Control": "max-age=60, stale-while-revalidate=120" } 
    });
    
  } catch (error) {
    console.error('Dossier API error:', error);
    
    // Fallback company data on error
    const fallbackCompany = {
      id: `company:${id}`,
      name: id[0]?.toUpperCase() + id.slice(1) || "Unknown",
      slug: id,
      logo: `https://dummyimage.com/256x256/0af/fff.png&text=${encodeURIComponent(id[0]?.toUpperCase() || 'C')}`,
      thesis: "AI-powered growth analysis",
      signalScore: 65,
      metrics: {
        revenue: [{ date: "2024-01-01", value: 2.1 }, { date: "2024-04-01", value: 2.6 }],
        commits: [{ date: "2024-01-01", value: 120 }, { date: "2024-02-01", value: 90 }],
        jobs: [{ date: "2024-01-01", value: 12 }, { date: "2024-02-01", value: 16 }]
      },
      repos: [{ url: "https://github.com/example/example", stars: 1234 }],
      timeline: [
        { id: "evt1", type: "funding", date: "2024-06-12", title: "Series B $60M", sources: [] },
        { id: "evt2", type: "hiring", date: "2024-07-05", title: "Key ML hires", sources: [] }
      ]
    };
    
    return NextResponse.json(fallbackCompany, { 
      headers: { "Cache-Control": "max-age=10, stale-while-revalidate=30" } 
    });
  }
}
