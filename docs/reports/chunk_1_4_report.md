# Chunk 1.4 — Dashboard Page Templates

**Status:** Implemented and committed; CI/security verification recorded below.  
**Scope:** Frontend-only analyst page templates for the eight workspace routes.

## Delivered
- Overview: preview KPIs, illustrative activity visualization, T1/T2/T3 composition, sample findings and disconnected collector health.
- AI Inventory: searchable/filterable sample inventory and local detail panel.
- Leak Alerts: severity/status/tier filters, selectable sample finding and masked evidence preview.
- Agent Graph: selectable conceptual nodes and explicitly illustrative edges.
- Compliance: framework selector and example control mapping; exports unavailable until backend exists.
- Data Sources: file selection (local only), live-capture boundary, opt-in gateway explanation and safe simulator preview.
- Policy Studio: browser-local candidate YAML editor, validation/simulation placeholders; no persistence or enforcement.
- System & Privacy: component connection status, privacy defaults, visibility tiers and platform caveats.
- Reusable page primitives, responsive layouts, and Playwright route/interaction coverage.

## Safety and truthfulness
All visible records and metrics are synthetic examples. No backend API, collector, database, SSE stream, risk calculation, policy engine, file upload, gateway, or simulator is connected. Controls are limited to local UI state. No command execution, live capture, real exfiltration, TLS MITM/decryption, raw prompt display, or raw secret persistence was introduced. T1 observed metadata, T2 derived inference, T3 authorized plaintext, DERIVED and UNAVAILABLE remain distinct.

## Verification
- Main base before implementation: `7877a2be494300e0679a384928820dc664430799`.
- CI and Security workflow results: pending final run at time of initial report; update this section with actual run IDs and conclusions after verification.

## Known limitations
- Graph is a conceptual preview, not React Flow or a graph backed by evidence.
- Compliance mappings are examples, not an assessment or certification.
- Policy validation and simulation require the backend.
- File selection is local browser UI only; no file bytes are uploaded or parsed.
- No live collectors or API data source exists in this frontend chunk.
