# ShadowLens Backend Architecture

**Status:** Design baseline with the M0 application lifecycle and canonical metadata-event intake implemented.  
**Source:** Master Specification sections 2, 4–7, 8–11 and 20.

## 1. Backend stack

Python 3.11+, FastAPI/Uvicorn, asyncio with bounded asyncio.Queue, Pydantic v2, SQLModel, SQLite WAL, structlog JSON logging, psutil, dpkt, optional Scapy, httpx for the explicit gateway, pytest, Hypothesis, Ruff and mypy.

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

This is a logical decomposition. The repository currently implements the canonical contracts, SQLite persistence, bounded event bus, collector supervisor, FastAPI lifespan, local bearer-token boundary, DB-aware health and canonical metadata-event intake. The remaining packages are planned work, not implied by this slice.

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

Implemented:
- Canonical Pydantic contracts, SQLite WAL persistence and the bounded async event bus.
- FastAPI lifespan initializes the database, starts the bus and collector supervisor, then stops producers, drains accepted events and disposes the engine in that order.
- `GET /api/health` reports database connectivity, queue counters and configured collector state. It is the explicit unauthenticated NFR-SEC-1 exception.
- `POST /api/events` requires bearer authentication and accepts a validated metadata-only canonical event. HTTP request schemas deliberately exclude `http.body_ref`; sensitive headers are redacted before queueing and persistence.
- First-run API token is generated locally and stored in `.shadowlens/access.token` with restrictive file/directory permissions. `SHADOWLENS_API_TOKEN` is an explicit operator override. API docs and OpenAPI are also protected.

Not yet implemented: multipart HAR/JSONL/PCAP parsers, real source collectors, normalization/detection, list/query APIs, SSE, remaining CLI actions (scan/ingest/simulate/demo/exports/forget), and the rest of the domain engines. The in-memory bus is not a durable queue: a process crash before a worker commits an accepted event can lose it. The official shadowlens serve command enforces loopback binding; operators who bypass it and launch Uvicorn directly can still override the socket bind address.

The previous `/api/v1/health` bootstrap route was replaced by the source-specified `/api/health` path. The auth exception follows the explicit NFR-SEC-1 rule rather than the broad API heading.


## 10. M0 application wiring boundary

The metadata-event route is an integration seam, not a replacement for `POST /api/ingest` multipart support. Upload parsing and source-specific normalization remain in the provider/collector milestone. A successful `202` means the event entered the bounded in-memory queue; it does not claim durable commit. Health exposes accepted, processed, failed, rejected and queued counts so operators can distinguish queue acceptance from persistence completion.


## 11. Structured logging and operational diagnostics

Application-owned operational logs use structlog and JSON on stderr. The redaction processor recursively removes values for sensitive field names (authorization, cookies, passwords, API keys, tokens, prompt/body/payload/content/raw fields), scrubs common bearer/API-key patterns in remaining strings, bounds strings and collections, and avoids arbitrary object representations.

The HTTP access middleware logs only method, matched route template, status, elapsed milliseconds and a server-generated request ID. It does not log query strings, request headers, client addresses, request bodies or payloads. The request ID is returned as `X-Request-ID`. Uvicorn's default access logger is disabled because it can include raw request targets and query strings.

Worker and collector failures log the exception class and counters/backoff only; exception messages are not emitted or retained in the collector supervisor's status. Unexpected API exceptions return a generic 500 body and a request ID rather than framework exception text. This logging boundary does not imply that arbitrary third-party or operating-system logs are captured or sanitized.


## 12. Local runtime configuration and CLI

The app.config.Settings model loads SHADOWLENS_* values and an optional .env from the current working directory. The defaults use 127.0.0.1:8000, a local .shadowlens data directory, SQLite, one event worker, a bounded queue and the configured JSON log level. The configured host accepts only localhost or a literal loopback IP. CORS origins are parsed as HTTP(S) origins and must also be localhost or a loopback IP; wildcard, remote, credential-bearing and path-bearing origins are rejected. CORS does not allow credentials and exposes only the request-ID response header.

The installed shadowlens console command currently supports:
- shadowlens init: create the local data directory, random owner-only bearer token when no operator token is configured, SQLite schema and a non-enforcing policy starter.
- shadowlens serve: run app.main:app through Uvicorn with a validated loopback bind and Uvicorn access logging disabled. --reload is intended for local development.

The policy starter is comments-only and intentionally activates no rules because a versioned policy schema/evaluator is not implemented yet. serve --live and serve --gateway return an explicit unavailable error; they do not start a packet capture or proxy. Scan, ingest, simulate, demo, benchmark, export and forget CLI actions remain future work.

SQLite database parent directories created by initialization use restrictive permissions on POSIX; the database file is set to owner read/write. Existing parent directory permissions are not changed. Token and starter policy files are also created with owner-only file permissions. These filesystem guarantees are POSIX-specific; Windows permission semantics differ.
