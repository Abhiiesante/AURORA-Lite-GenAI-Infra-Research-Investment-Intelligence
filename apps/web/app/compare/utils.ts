export type Weights = Record<string, number>;
export type Metrics = Record<string, number>;

export function computeComposite(weights: Weights, metrics: Metrics): number {
  const entries = Object.entries(weights);
  if (entries.length === 0) return 0;
  const sum = entries.reduce((s, [, w]) => s + (w || 0), 0) || 1;
  let score = 0;
  for (const [k, w] of entries) {
    const v = metrics[k] ?? 0;
    score += (w / sum) * v;
  }
  // clamp 0..1
  return Math.max(0, Math.min(1, score));
}

export function computeTorque(leftScore: number, rightScore: number): number {
  // Positive torque tilts right; clamp to [-1, 1]
  const t = rightScore - leftScore;
  return Math.max(-1, Math.min(1, t));
}
