# AURORA-Lite Web

Next.js app for the UI. Requires NEXT_PUBLIC_API_URL to reach the API.

## Market Map KG toggle

- Page: `/market-map`
- Toggle: "Use KG source" switches the data source for the market graph to the Knowledge Graph by appending `source=kg` to the API call (`/market/realtime`).
- Persistence: The toggle state is saved in `localStorage` (key: `marketMapUseKG`) and applied on initial load.
- Views: Saved views also persist the KG mode so reloading a view restores your preferred source.

### Filters, URL sync and utilities

- Filters: Segment and Min signal fields refine the graph; press Enter in either field or click Apply to reload.
- URL sync: segment, min_signal and source=kg are read on first load and written back on Apply/toggle, enabling shareable links.
- Reset: Clears filters and removes query params, reloading defaults.
- Copy Link: Copies the current URL (with active filters) to the clipboard.
