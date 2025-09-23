# Trends Exports & Audio

This page summarizes the export options and audio controls available on the Trends page.

## Exports

- Snapshot (PNG): Captures the hero canvas and overlays as a bitmap.
- Export PDF: Generates an A4 landscape PDF with the snapshot and a footer.
- Export SVG: Creates a vector overlay of selected/compare labels, connectors, lasso rectangle, and timeline markers. This intentionally does not vectorize the 3D scene.
- Export Bundle (PDF+SVG): Two-page PDF – Page 1 is the hero PNG; Page 2 is a rasterized version of the SVG overlay for easy sharing.

Notes:
- SVG export aligns to the current hero viewport size.
- If you need the raw SVG file alongside the PDF bundle, use the “Export SVG” button separately.

## Audio

- A mute toggle (🔊/🔇) and volume slider are available in the top-right controls.
- Preferences persist per browser via localStorage.
- Placeholder tones are replaced with small branded cues internally; for production-quality sounds, place higher-fidelity assets under `public/audio/*.wav` and point the Howler sources there.
