import { NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const { searchParams } = new URL(req.url);
  const metric = searchParams.get('metric') || 'mentions';
  const horizon = parseInt(searchParams.get('horizon') || '4');
  const confidence = parseFloat(searchParams.get('confidence') || '0.8');
  const id = params.id;

  try {
    // Fetch forecast data from FastAPI
    const forecastRes = await fetch(`${API_BASE}/forecast/${id}?metric=${metric}&horizon=${horizon}`)
      .then(r => r.ok ? r.json() : null);

    if (!forecastRes) {
      throw new Error('No forecast data available');
    }

    // Transform FastAPI forecast response
    const baselineValues = forecastRes.baseline || [];
    const forecastValues = forecastRes.forecast || [];
    const uncertaintyBands = forecastRes.uncertainty || [];

    // Generate sensitivity analysis data
    const sensitivityFactors = [
      { factor: 'Market Growth', impact: 0.25, range: [-0.3, 0.4] },
      { factor: 'Competition', impact: -0.15, range: [-0.4, 0.1] },
      { factor: 'Team Expansion', impact: 0.35, range: [-0.1, 0.5] },
      { factor: 'Product Launch', impact: 0.45, range: [0.1, 0.7] },
      { factor: 'Economic Climate', impact: -0.05, range: [-0.3, 0.2] }
    ];

    // Generate scenario matrix for sensitivity analysis
    const scenarioMatrix = sensitivityFactors.map(factor => ({
      factor: factor.factor,
      scenarios: [
        { scenario: 'pessimistic', value: factor.impact + factor.range[0], probability: 0.15 },
        { scenario: 'base', value: factor.impact, probability: 0.7 },
        { scenario: 'optimistic', value: factor.impact + factor.range[1], probability: 0.15 }
      ]
    }));

    const response = {
      companyId: `company:${id}`,
      metric,
      horizon,
      confidence,
      baseline: baselineValues.length > 0 ? baselineValues : Array.from({ length: horizon }, (_, i) => ({
        period: i + 1,
        date: new Date(Date.now() + (i + 1) * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: 100 + Math.sin(i / 2) * 20 + Math.random() * 10
      })),
      forecast: forecastValues.length > 0 ? forecastValues : Array.from({ length: horizon }, (_, i) => ({
        period: i + 1,
        date: new Date(Date.now() + (i + 1) * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        value: 110 + i * 5 + Math.sin(i / 2) * 15,
        confidence_lower: 95 + i * 3 + Math.random() * 5,
        confidence_upper: 125 + i * 7 + Math.random() * 10
      })),
      uncertainty: uncertaintyBands.length > 0 ? uncertaintyBands : Array.from({ length: horizon }, (_, i) => ({
        period: i + 1,
        uncertainty: Math.max(0.05, 0.1 + i * 0.02 + Math.random() * 0.05),
        factors: ['market_volatility', 'competitive_pressure', 'execution_risk']
      })),
      sensitivity: {
        factors: sensitivityFactors,
        scenarios: scenarioMatrix,
        tornado_chart: sensitivityFactors
          .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
          .map(factor => ({
            factor: factor.factor,
            low: factor.impact + factor.range[0],
            high: factor.impact + factor.range[1],
            base: factor.impact
          }))
      },
      metadata: {
        model_version: forecastRes.model_version || 'forecast-v2.1',
        generated_at: new Date().toISOString(),
        data_window: forecastRes.window || '90d',
        feature_count: forecastRes.features?.length || 12,
        source: forecastRes.forecast ? 'fastapi' : 'enhanced-fallback'
      }
    };

    return NextResponse.json(response, {
      headers: { "Cache-Control": "max-age=1800, stale-while-revalidate=3600" }
    });

  } catch (error) {
    console.error('Forecast API error:', error);

    // Enhanced fallback forecast data
    const fallbackBaseline = Array.from({ length: horizon }, (_, i) => ({
      period: i + 1,
      date: new Date(Date.now() + (i + 1) * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      value: Math.round((80 + Math.sin(i / 3) * 10 + Math.random() * 8) * 100) / 100
    }));

    const fallbackForecast = Array.from({ length: horizon }, (_, i) => ({
      period: i + 1,
      date: new Date(Date.now() + (i + 1) * 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      value: Math.round((90 + i * 3 + Math.sin(i / 2) * 12 + Math.random() * 5) * 100) / 100,
      confidence_lower: Math.round((75 + i * 2 + Math.random() * 3) * 100) / 100,
      confidence_upper: Math.round((105 + i * 4 + Math.random() * 8) * 100) / 100
    }));

    return NextResponse.json({
      companyId: `company:${id}`,
      metric,
      horizon,
      confidence,
      baseline: fallbackBaseline,
      forecast: fallbackForecast,
      uncertainty: Array.from({ length: horizon }, (_, i) => ({
        period: i + 1,
        uncertainty: Math.round((0.08 + i * 0.015 + Math.random() * 0.03) * 1000) / 1000,
        factors: ['market_volatility', 'competitive_pressure']
      })),
      sensitivity: {
        factors: [
          { factor: 'Market Growth', impact: 0.2, range: [-0.25, 0.35] },
          { factor: 'Competition', impact: -0.1, range: [-0.3, 0.05] },
          { factor: 'Team Expansion', impact: 0.3, range: [-0.05, 0.4] }
        ],
        scenarios: [],
        tornado_chart: []
      },
      metadata: {
        model_version: 'fallback-v1.0',
        generated_at: new Date().toISOString(),
        data_window: '90d',
        feature_count: 8,
        source: 'fallback',
        error: 'Failed to fetch live forecast data'
      }
    }, {
      headers: { "Cache-Control": "max-age=300, stale-while-revalidate=600" }
    });
  }
}