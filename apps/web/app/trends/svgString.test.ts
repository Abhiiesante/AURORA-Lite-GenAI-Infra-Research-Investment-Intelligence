import { buildSvgString } from './svgString';

describe('buildSvgString', () => {
  it('returns non-empty SVG string for basic inputs', () => {
    const svg = buildSvgString({
      width: 800,
      height: 400,
      points: [
        { x: 100, y: 100, id: 'a', label: 'Alpha', selected: true },
        { x: 200, y: 180, id: 'b', label: 'Beta', compare: true },
      ],
      lasso: { x0: 80, y0: 80, x1: 220, y1: 200 },
      markers: [{ t: 0.25, label: 'cp' }],
      title: 'Test',
      asOf: '2025-09-21',
    });
    expect(typeof svg).toBe('string');
    expect(svg.length).toBeGreaterThan(50);
    expect(svg).toContain('<svg');
  });
});
