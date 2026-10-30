# ShadowLens Backend Architecture

**Status:** Design baseline; implementation is not implied.  
**Source:** Master Specification sections 2, 4–7, 8–11 and 20.

## 1. Backend stack

Python 3.11+, FastAPI/Uvicorn, asyncio with bounded asyncio.Queue, Pydantic v2, SQLModel, SQLite WAL, psutil, dpkt, optional Scapy, httpx for the explicit gateway, pytest, Hypothesis, Ruff and mypy.

## 2. Package boundaries

| Package | Owns | Main inputs/outputs |
|---|---|---|
| app/config | Settings, policy config, local paths, feature flags | Validated settings and policy |
| app/models | Canonical Event, Finding, Tool, Evidence, enums and persistence models | Shared domain contracts |
| app/collectors | Socket, PCAP, log, loopback, gateway, config and agent adapters | Source observations → Event |
| app/core/providers | Provider registry and classifier | Event metadata → provider classification |
| app/core/normalize | Safe normalization and bounded decoding | Transient payload → normalized inspection candidates |
| app/core/detect | Secret, entropy, PII, proprietary-data, canary rules | Candidates → deterministic findings |
| app/core/agent | Tool-call, shell, filesystem, network, autonomy and chain logic | Structured agent events → findings |
| app/core/shape | T2 flow-shape baselines | Metadata windows → shape findings |
| app/core/risk | Risk calculation and explanation | Findings/context → deterministic scores |
| app/core/compliance | Versioned control mapping | Rule IDs → informational controls/posture |
| app/core/triage | Optional LLM client, privacy filter and fallback | Redacted finding DTO → advisory only |
| app/bus | Bounded event queue, worker lifecycle and supervision | Canonical events to processing workers |
| app/services | Use-case orchestration and transaction boundaries | API/CLI commands → domain operations |
| app/repositories | SQLModel/SQLite persistence | Domain records ↔ storage |
| app/api | Auth, routers, SSE, request/response schemas | HTTP → services |
| app/export | BOM, SARIF, CEF and HTML exporters | Redacted persisted data → export |
| app/sim | Synthetic scenario fixtures and replay | Scenario → canonical event stream |
| app/cli | init, serve, simulate/demo, benchmark and forget commands | Operator commands → services |

This is a logical decomposition. The current repository has only a minimal FastAPI bootstrap; these packages are planned, not implemented.

## 3. Layering and import rules

1. Domain contracts and pure core logic must not import FastAPI, SQLModel sessions or frontend code.
2. Collectors may depend on contracts and adapter utilities; they may not call risk or write findings directly.
3. Services orchestrate pure core logic and repositories.
4. API routers validate/authenticate and delegate to services.
5. Repositories own SQL statements and transactions.
6. Optional providers implement narrow protocols; missing providers must not prevent startup.
7. No circular imports; shared types live in app/models or small protocol modules.

## 4. Event processing lifecycle

1. Adapter collects source data and labels source/tier.
2. Adapter constructs a canonical Event; unavailable fields remain absent/UNAVAILABLE.
3. Event enters a bounded queue; overflow is observable and handled by the documented backpressure policy.
4. Normalizer validates and performs bounded decoding using a transient buffer.
5. Provider classifier enriches provider/kind/sanction context.
6. Relevant deterministic inspectors and agent/shape analyzers produce findings.
7. Correlator links related events/findings.
8. Risk and compliance derive reproducible outputs.
9. Repository transaction persists normalized metadata and redacted evidence only.
10. API/SSE notifies dashboard clients; optional triage runs asynchronously after redaction.

## 5. Persistence boundary

Use SQLite WAL and SQLModel. The source schema identifies assets, ai_tools, events, findings, finding_events, secret_vault, canaries, risk_snapshots and policies. Add migrations and indexes without persisting raw bodies. Use transactions for event/finding/evidence relationships and batched writes as specified by NFR-REL-2.

## 6. API ownership

Implement the source REST inventory under /api: summary, events, tools, findings, graph, risk explanation, compliance, ingest, simulate, canary, policy simulation, export, stream and health. Protect API routes with the local bearer token; /api/health is the explicit NFR-SEC-1 exception. Resolve the source's broad "all require token" heading versus the health exception in code and tests by following the explicit NFR exception.

## 7. Failure handling

- Collector exceptions are isolated; supervisor restarts with backoff.
- Permission failures degrade to partial visibility and must not stop other collectors.
- Queue saturation must not silently drop events; define bounded behavior, counters and health visibility before implementation.
- Parser failures return structured errors; untrusted uploads have strict size and resource bounds.
- Database failures surface degraded health; do not report a successful ingest if persistence failed.
- Optional triage failure falls back to deterministic rule-based advice.
- Unknown provider and unavailable telemetry remain explicit states.

## 8. Security controls

Loopback binding, bearer token, restrictive CORS/CSP, restrictive token/database file permissions, upload validation, bounded parsers, regex time budgets, no raw payload logs, redacted exports, explicit gateway allowlist and SSRF prevention.

## 9. Current implementation delta

Implemented: FastAPI app bootstrap and process-level /api/v1/health endpoint only.  
Not yet implemented: canonical models, storage, queue, collector protocols, services, API route inventory, auth, migrations, event pipeline and domain engines.  
The current /api/v1/health route differs from the spec's /api/health and must be reconciled as a deliberate API-prefix decision in M0.
