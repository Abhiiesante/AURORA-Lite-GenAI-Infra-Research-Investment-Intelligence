# Compare (Page 6)

Production brief notes:
- 3D balance beam metaphor with deterministic tilt mapping from composite score delta; respects prefers-reduced-motion.
- Right rail controls for metric weights via draggable token rows and slider fallback; live clink/grab/settle audio cues; mute/volume persisted.
- Dev-only Next.js API routes for local iteration: create compare session, update weights, snapshot stub.
- Exports and provenance planned (PNG/SVG/PDF bundle) in follow-ups.

Dev endpoints (local):
- POST /api/compare { companies: string[], weights?: Record<string,number> }
- GET /api/compare/:id
- POST /api/compare/:id/weight { metric: string, delta: number }
- POST /api/compare/:id/snapshot

Testing:
- Jest includes app/compare; utils.test validates composite clamping and torque bounds.

Next:
- Hook to real backend endpoints, drag-and-drop slab placement, shaders (rim/metal), snapshot export, and richer narrative.
