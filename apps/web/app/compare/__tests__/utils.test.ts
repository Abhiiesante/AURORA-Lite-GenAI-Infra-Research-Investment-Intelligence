import { computeComposite, computeTorque } from '../utils';

describe('utils', () => {
  test('computeComposite clamps and normalizes', () => {
    const weights = { a: 0.5, b: 0.5 };
    const metrics = { a: 1, b: 1 };
    expect(computeComposite(weights, metrics)).toBeCloseTo(1);
    const metrics2 = { a: 0, b: 0 };
    expect(computeComposite(weights, metrics2)).toBeCloseTo(0);
    const metrics3 = { a: 2, b: -1 };
    const v = computeComposite(weights, metrics3);
    expect(v).toBeGreaterThanOrEqual(0);
    expect(v).toBeLessThanOrEqual(1);
  });

  test('computeTorque is bounded -1..1', () => {
    expect(computeTorque(0, 1)).toBe(1);
    expect(computeTorque(1, 0)).toBe(-1);
    expect(computeTorque(0.2, 0.25)).toBeCloseTo(0.05, 2);
  });
});
