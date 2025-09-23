import { buildCompareSvg } from '../svgString';

describe('buildCompareSvg', () => {
  it('produces an SVG string with header and weights', () => {
    const svg = buildCompareSvg({
      width: 800,
      height: 450,
      title: 'Comparator — Weigh the Options',
      asOf: 'now',
      leftName: 'Alpha',
      rightName: 'Beta',
      leftScore: 0.62,
      rightScore: 0.58,
      weights: { revenue_growth: 0.4, arr: 0.2 },
    });
    expect(svg).toContain('<svg');
    expect(svg).toContain('Comparator — Weigh the Options');
    expect(svg).toContain('Weights');
  });
});
