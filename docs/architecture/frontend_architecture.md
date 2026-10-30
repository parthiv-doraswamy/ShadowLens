# ShadowLens Frontend Architecture

**Status:** Design baseline; current React app is only a bootstrap screen.  
**Source:** Master Specification sections 2, 4, 6.8, 7.1, 10, 11 and 20.

## 1. Stack and responsibility

React, TypeScript and Vite form a separate analyst client. Tailwind CSS and shadcn/ui are the specified component baseline. Recharts owns charts; React Flow owns the agent permission graph. The frontend consumes FastAPI contracts and does not implement detection, scoring or policy logic.

## 2. Route ownership

| Route / page | Primary responsibility | API source |
|---|---|---|
| Overview | Risk/trend, tool counts, critical findings, exfil activity, tier mix, top providers/processes and live feed | GET /api/summary, /api/events, /api/stream |
| Inventory | AI tool instances, provider, host, first/last seen, sanctioned state, autonomy/risk and timeline drawer | GET /api/tools; PATCH /api/tools/{id} |
| Leak Alerts | Finding filters, masked evidence, rule explanation, confidence, controls, triage and status actions | GET/PATCH /api/findings; POST /api/findings/{id}/triage |
| Agent / Permission Graph | Evidence-backed process, agent, MCP, file-scope and network-host graph | GET /api/graph |
| Risk detail | Score decomposition, top drivers and projected quick wins | GET /api/risk/{scope}/{id}/explain |
| Compliance | Framework posture, control mapping and report exports | GET /api/compliance; GET /api/export/{format} |
| Ingest | PCAP/HAR/JSONL upload, capability/coverage, scenario launcher, gateway setup and canary creation | POST /api/ingest, /api/simulate/{scenario}, /api/canary |
| Policy Studio | YAML validation, simulation and diff; candidate policy does not activate implicitly | POST /api/policy/simulate |
| System / Privacy | Local-only mode, raw-payload retention status, triage mode, collector health and visibility | GET /api/health |

These are logical routes; exact client-side URL paths remain to be selected during UI implementation.

## 3. Shared UI modules

- Typed API client with centralized auth, error parsing, timeout and cancellation.
- Domain types generated/validated against OpenAPI where practical.
- Reusable tables, filters, severity/status/tier badges, evidence cards, dialogs, drawers, tabs and forms.
- Explicit loading, empty, partial-permission, offline, error and retry states.
- SSE client with reconnect/backoff and clear disconnected state.
- Theme tokens and dark/light theme support.
- Keyboard focus, accessible names, reduced-motion handling and WCAG AA contrast.
- Demo mode is explicitly labelled; API failure must never silently fall back to demo metrics.

## 4. Evidence presentation rules

Every finding view shows source, visibility tier, confidence, detector/rule ID/version and evidence reference. T1/T2/T3 are visibly distinct. DERIVED and UNAVAILABLE are not displayed as observation tiers. T2 is phrased as inference, not content inspection. Raw values are never displayed; masked previews and redacted context are used.

## 5. State and action ownership

The API/database is authoritative for persisted tools, findings, policy and risk. UI state owns transient filters, sort, pagination, open drawers and unsaved editor text. Status changes and sanction updates call the API and refresh from server state. Policy simulation is read-only until a separate explicit apply workflow is defined. Incident replay is read-only.

## 6. API failure and empty-state behavior

- Empty data shows an honest empty state and Run Demo action where appropriate.
- Permission-limited collection shows partial coverage and source limitations.
- Failed API requests show retry/error state, not fabricated data.
- Missing Featherless credentials show no-LLM/rule-based mode, not a broken core dashboard.
- SSE interruption shows stale/disconnected status and reconnect behavior.

## 7. Current implementation delta

Current frontend: one App component showing bootstrap status. No dashboard routes, design system, API client, chart, graph or analyst workflows are implemented yet. Frontend design chunks are scheduled independently and must integrate only after canonical contracts stabilize.
