# ShadowLens Implementation Backlog

**Source:** `ShadowLens_Unified_Master_Specification.md`, especially sections 15, 17, 20, 21 and 22.  
**Planning model:** Section 17 milestone sequence M0–M8 is the primary detailed delivery order. Section 20 supplies vertical-slice phase gates A–G. The work-allocation prompt pack supplies chunk-sized execution sequencing.  
**Current branch:** `feat/provider-registry-req-disc-001` (Chunk 3.1 implementation branch; `main` remains unchanged pending review/CI).  
**Current state:** Chunks 0.1–0.4, 1.1–1.4 and 2.1–2.6 are implemented. Chunk 3.1 (REQ-DISC-001 provider registry/classifier) is implemented on the current feature branch and awaiting pull-request CI. Provider collectors, REQ-DISC-002 sanction policy, detection and dashboard/API integration remain pending.

## 1. Delivery principles

1. Follow the source milestone order; do not start a later milestone before the previous milestone's acceptance tests are green.
2. Tests are written first for each implementation task. A requirement is not done without a requirement ID, implementation, test and traceability row.
3. The core product must work without LLM credentials.
4. Prefer complete end-to-end vertical slices over broad nonfunctional feature placeholders.
5. Keep advanced integrations from delaying the MVP; honor explicit phase gates and record the source priority conflicts.
6. Keep all collection local-first, least-privilege and transparent about coverage; never claim visibility the operating system/source does not provide.

## 2. Milestone backlog — source section 17

### M0 — Foundations (source estimate: 0.5 day)

**Deliverables**
- Repository/package baseline, CI, Pydantic canonical event/finding models.
- SQLite persistence layer and WAL configuration.
- Bounded asynchronous event bus.
- `init`/`serve` skeleton and local bearer-token setup.
- Health/coverage endpoint.
- Structured logs with secret redaction.

**Primary work packages**
- M0.1 Confirm package/module layout against source section 11 and this repository's current backend/frontend scaffold.
- M0.2 Implement strict Pydantic canonical event, finding, tool, evidence, visibility and coverage contracts.
- M0.3 Implement SQLModel/SQLite WAL setup, migrations, indexes, safe startup/shutdown and transaction behavior.
- M0.4 Implement bounded asyncio queue, collector protocol, worker supervisor, backpressure and shutdown behavior.
- M0.5 Implement local token generation/storage, protected API route baseline, request/error handling and health/coverage status.
- M0.6 Implement structured logging/redaction and prove test secrets do not appear in DB/logs.

**Requirements / coverage:** Foundation and cross-cutting support for all REQ IDs; section 5 domain model; NFR-REL-1, NFR-REL-2, NFR-SEC-1. No functional requirement ID is explicitly assigned to the whole M0 platform foundation.

**Exit gate:** Clean local startup; health endpoint reports DB and adapter state; fixture event traverses ingestion → normalization → SQLite; raw test secret absent from logs/DB; CI green.

**Current status:** PARTIAL. Repo/CI/frontend/backend scaffold and one health test exist. Not yet implemented: canonical event/finding models, SQLite layer, bounded event queue, local bearer token, real adapter status, DB-aware health. Current bootstrap route is `/api/v1/health`; spec lists `/api/health`. Resolve path/prefix intentionally before claiming NFR-SEC-1 compliance.

### M1 — Detection core (source estimate: 1.5 days; highest priority)

**Deliverables**
- Validators, entropy, secret + PII rules in YAML with tests.
- Normalizer, canary, redaction/HMAC vault and benchmark harness.

**Requirements:** REQ-DET-001 through REQ-DET-008; REQ-PRIV-001 through REQ-PRIV-006; NOV-4, NOV-11, NOV-12; NFR-TEST-1; section 12 benchmark.

**Work packages**
- M1.1 Normalization/decoding: bounded JSON string extraction, unescape, base64/URL/gzip depth ≤3, size ≤5 MB.
- M1.2 Secret rule registry: all SEC-* families; validators and positive/negative fixture vectors.
- M1.3 Entropy engine: charset normalization, thresholds, identifier/dictionary false-positive rejection.
- M1.4 PII validators: email/phone/card/Aadhaar/PAN/SSN/IBAN/internal IP and context-gated name/DOB/bulk PII.
- M1.5 Proprietary/internal data heuristics and masked evidence.
- M1.6 Privacy storage: transient payload handling, HMAC vault, typed context redaction, redacted outputs, forget command.
- M1.7 Canary generation/detection with explicit user-selected planting directory and approval.
- M1.8 Deduplication/suppression and streaming chunk-boundary detection.
- M1.9 Synthetic benchmark corpus + CLI + report + Hypothesis properties.

**Exit gate:** Every rule has positive/negative tests; secret/PII results reproducible; raw values absent from persistence/log/API/export; benchmark gates pass; decode depth bounded.

### M2 — Providers and collectors (source estimate: 1 day)

**Deliverables**
- Provider registry/classifier.
- HAR/JSONL log ingestion.
- PCAP metadata collection (SNI/JA4/HTTP/DNS).
- Socket/process collector.

**Requirements:** REQ-COL-001, REQ-COL-002, REQ-COL-003, REQ-DISC-001, REQ-DISC-002; source traceability also includes REQ-COL-005 test path for later gateway work.  
**Additional:** NFR-PERF-2, NFR-PORT-1; NOV-1 visibility contract.

**Work packages**
- M2.1 Versioned/hot-reloadable provider registry with required provider coverage, positive/negative tests and unknown provisional classification.
- M2.2 Socket/process metadata adapter with permission degradation, process-exit/race handling and coverage.
- M2.3 HAR/mitmproxy JSON/nginx-squid JSONL/mock-log parser with safe upload validation and redaction handoff.
- M2.4 Offline PCAP parsing for TCP flows, DNS, TLS ClientHello SNI/ALPN and plaintext HTTP; no TLS body claims.
- M2.5 Provider sanction policy and 24-hour finding deduplication.
- M2.6 Local LLM port detection and visibility/source-mode indicators.

**Exit gate:** Positive/negative provider tests pass; local model endpoints identified from configured indicators; unknown endpoints remain provisional; permission failures visible and isolated.

### M3 — Agent analysis (source estimate: 1.5 days)

**Deliverables**
- Tool-call extractors.
- Shell/filesystem/network rules.
- Path canonicalization and autonomy.
- Injection-to-exfil correlator.
- Config scanner and MCP risk.

**Requirements:** REQ-COL-006, REQ-DISC-003, REQ-DISC-004, REQ-AGT-001 through REQ-AGT-007; NOV-2, NOV-3, NOV-6.

**Work packages**
- M3.1 Structured agent event contracts and supported source adapters.
- M3.2 Tool-call extraction across OpenAI, Anthropic, Ollama, MCP and LangChain formats.
- M3.3 Shell command parser and risk rule registry; chained-command segmentation.
- M3.4 Safe path canonicalizer and sensitive-file/project-root rules.
- M3.5 Network destination and post-sensitive-read correlation rules.
- M3.6 Autonomy A0–A4 calculation.
- M3.7 MCP capability/root/transport/package/publisher analysis.
- M3.8 Opt-in, read-only, allowlisted AI config discovery and browser-extension manifest discovery.
- M3.9 120-second injection-to-exfil correlator and ordered evidence timeline.

**Exit gate:** Supported fixture events produce expected findings; no simulated shell execution; every finding links source audit event(s); unsupported sources explicitly unavailable.

### M4 — Risk, compliance and shape (source estimate: 1 day)

**Deliverables**
- Deterministic risk engine and explanation.
- Provider/tool/host risk views.
- Deduplication/suppression integration.
- Compliance control mapper.
- Flow-shape analyzer and AI-BOM.

**Requirements:** REQ-SHP-001, REQ-RSK-001, REQ-RSK-002, REQ-CMP-001, REQ-CMP-002; NOV-5, NOV-7, NOV-8, NOV-9.

**Work packages**
- M4.1 Implement section 8.1 risk math exactly; version weights and explanations.
- M4.2 Shape baselines using rolling median/MAD for seven days and thresholds in section 6.5/8.3.
- M4.3 Versioned control mapping and posture reports, labelled informational.
- M4.4 CycloneDX 1.6 AI-BOM component/dependency export.
- M4.5 API/UI explainability with contribution table, top-five drivers and projected quick wins.

**Exit gate:** Identical events + same policy produce identical score; explanation exposed; mappings are versioned/informational; tests for shape thresholds and risk bounds pass.

### M5 — Dashboard (source estimate: 2 days)

**Deliverables**
- Overview, Inventory, Alerts, Graph, Compliance and Ingest pages.
- Evidence cards, tier badges, privacy/coverage panel and SSE live feed.
- Incident/replay user journeys.

**Requirements:** REQ-UI-001 through REQ-UI-009; REQ-RSK-002 and API/UI relationships; NOV-1, NOV-3, NOV-8, NOV-9.

**Work packages**
- M5.1 Shared component system with keyboard/focus/reduced-motion/accessibility foundations.
- M5.2 Overview real API-backed KPIs, trends and SSE.
- M5.3 AI inventory with sanctioned status, autonomy/risk and detail timeline.
- M5.4 Findings list, filters, masked evidence, status actions and triage panel.
- M5.5 React Flow evidence-backed permission graph.
- M5.6 Compliance posture/control view and report actions.
- M5.7 Ingest UI, coverage status and safe capability controls.
- M5.8 Privacy badge, partial/error/loading/empty states and accessible themes.
- M5.9 Playwright analyst workflow across API-backed screens.

**Exit gate:** Graph nodes/edges link to real evidence; filters/status work; replay is read-only; empty/error/partial-permission/no-LLM states are usable.

### M6 — Gateway, loopback and simulator (source estimate: 1 day)

**Deliverables**
- Opt-in Lens Gateway.
- Optional Scapy loopback capture.
- `simulate`/`demo` and S1–S10 scenarios.

**Requirements:** REQ-COL-004, REQ-COL-005, REQ-COL-007; REQ-DET-006; scenario coverage S1–S10; NOV-4, NOV-13.

**Work packages**
- M6.1 Synthetic scenario definitions and deterministic fixture event generator.
- M6.2 Safe PCAP/mock-log generation and replay.
- M6.3 Implement at least 8 scenarios; target all 10 source scenarios.
- M6.4 Gateway only if explicit opt-in, upstream allowlist, loopback-only, no body persistence, streaming and SSRF protections pass.
- M6.5 Optional loopback sniffing only where platform/permissions support; T1 fallback and clear coverage warning.

**Exit gate:** `shadowlens demo` runs offline; no destructive shell execution or real exfiltration; gateway restrictions and non-persistence verified. **Priority conflict:** source section 6 marks COL-004/005 P0 while section 21 places the optional live capture/gateway compatibility in P2.

### M7 — LLM triage and policy (source estimate: 0.5 day)

**Deliverables**
- Featherless/Ollama optional advisor.
- Guardrails and deterministic fallback.
- Policy simulation.

**Requirements:** REQ-TRI-001, REQ-TRI-002, REQ-POL-001, REQ-POL-002; NOV-10, NOV-14.

**Work packages**
- M7.1 Validated policy YAML and hot reload.
- M7.2 Candidate-policy simulation with isolated replay and diff output.
- M7.3 Privacy filter sending only the specified masked/redacted context.
- M7.4 Optional Featherless and local Ollama clients; configurable model; 8-second timeout/rate limit/cache.
- M7.5 Schema-validated triage output, injection-resistant snippet handling, deterministic fallback and deterministic override.

**Exit gate:** No-key/no-network fallback works; verified deterministic findings win; advisor cannot change detection or risk results; policy simulation does not mutate live state.

### M8 — Polish and release hardening (source estimate: 0.5 day)

**Deliverables**
- README/GIF demo, exports (SARIF/CEF/HTML), performance tests and security review.
- Clean install and reproducible demo.

**Requirements:** REQ-CMP-002 and export API; NOV-7, NOV-15; all NFRs and section 22 DoD.

**Work packages**
- M8.1 Packaging and clean-install verification; CLI quick start under 5 commands.
- M8.2 AI-BOM, SARIF, CEF and HTML exports using redacted real records.
- M8.3 Any NOV-15 syslog/JSONL/webhook/ticket work accepted as stretch scope only.
- M8.4 Run performance and security suites; record hardware/fixtures/methodology.
- M8.5 Complete independent spec/traceability audit and limitations documentation.

**Exit gate:** Section 22 final Definition of Done and all NFR gates pass. Do not claim release when any P0 requirement is unimplemented or untested.

## 3. Requirement-to-milestone ownership

| Requirement group | Primary milestone | Cross-milestone dependencies |
|---|---|---|
| REQ-COL-001/002/003 | M2 | M0 canonical event + M1 redaction handoff |
| REQ-COL-004/005 | M6 | M0 pipeline, M1 detector, M2 provider/normalizer |
| REQ-COL-006 | M3 | M0 canonical agent event model |
| REQ-COL-007 | M6 | M0 pipeline, M1 rules, M5 dashboard |
| REQ-DISC-001/002 | M2 | M0 models/policy |
| REQ-DISC-003/004 | M3 | M2 provider registry |
| REQ-DET-001–008 | M1 | M0 canonical finding/evidence models |
| REQ-AGT-001–007 | M3 | M0 contracts; M1 evidence/redaction |
| REQ-SHP-001 | M4 | M2 metadata and baselines |
| REQ-RSK-001/002 | M4 | M1 findings, M3 autonomy |
| REQ-CMP-001/002 | M4 | M1 rule IDs, M4 findings/risk |
| REQ-TRI-001/002 | M7 | M1 deterministic findings/redaction |
| REQ-POL-001/002 | M7 | M0 settings/storage; M4 score functions |
| REQ-UI-001–009 | M5 | M0 API foundation; M2–M4 services |
| REQ-PRIV-001–006 | M1 baseline, enforced throughout | Every collector, service, API and export |
| NFR-PERF/REL/SEC/PORT/TEST/DOC | M0 baseline; validated M8 | Relevant owning milestones |

## 4. Spec slicing — section 15

The specification asks that `specs/` be created with these slices. This is a documentation-generation task; these are not present in the current repository yet.

| Slice | Source content | Main backlog |
|---|---|---|
| `00-constitution.md` | Sections 1–3 and 9 | Global invariants, stack, non-goals and privacy |
| `01-domain-model.md` | Section 5 + schemas | M0 |
| `02-collectors.md` | REQ-COL-* | M2/M6 |
| `03-discovery.md` | REQ-DISC-*, REQ-SHP-* | M2/M3/M4 |
| `04-detection.md` | REQ-DET-*, section 8.2, section 12 | M1 |
| `05-agent-analysis.md` | REQ-AGT-*, section 8.4 | M3 |
| `06-risk-compliance.md` | REQ-RSK/CMP/TRI/POL, sections 8.1 and 9.3 | M4/M7 |
| `07-api-ui.md` | REQ-UI-*, section 7.1 | M0/M5 |
| `08-sim-bench.md` | REQ-COL-007, sections 12 and 14 | M1/M6 |
| `tasks.md` | Section 17 milestone checklist with IDs | All |

**Per-requirement coding prompt from source:** implement exact IDs per slice; write tests from acceptance criteria first; do not add unspecified behavior; record ambiguity as a question.

## 5. Chunk sequencing aligned with work-allocation plan

After this extraction chunk, the requested execution order remains:
1. Chunk 0.3 — architecture and traceability.
2. Chunk 0.4 — CI/security automation.
3. Phase 1 frontend templates (1.1–1.4), separate from backend feature foundation after contracts stabilize.
4. Phase 2 backend foundation (2.1–2.5).
5. Phases 3–8 feature milestones, mapped against M1–M8 above.
6. Phase 9 user-gated work and final independent audit.

The master spec's milestone gates take precedence over any schedule estimate; these estimates are not delivery guarantees.

## 6. Current repository execution status (after Chunk 1.1 design system)

| Item | State after Chunk 0.3 audit |
|---|---|
| Root master spec copied into repository | Complete |
| Requirements catalog | Complete |
| Acceptance criteria | Complete |
| Implementation backlog | Complete |
| Human approval gates | Complete |
| Architecture and traceability (Chunk 0.3) | Complete and audited — 7 architecture documents + full traceability matrix; see docs/reports/chunk_0_3_report.md |
| CI/security automation (Chunk 0.4) | CI passed (Ruff/mypy/pytest/typecheck/build/Playwright); Gitleaks and Semgrep passed; both initial CodeQL jobs failed; `security-events: write` was added to permit SARIF upload and the follow-up run is pending. Dependabot is configured and has opened six update PRs; see docs/reports/chunk_0_4_report.md |
| Frontend design system (Chunk 1.1) | Implemented and verified: tokens, reusable primitives, /design-system showcase, responsive/accessibility foundations and Playwright interactions; CI and security workflows green on main; see docs/reports/chunk_1_1_report.md |
| Repository scaffold/CI | Complete for bootstrap scope |
| M0 foundation | Partial only; see Chunk 0.1 report |
| Product requirements REQ-* | Not implemented/verified yet |
| Traceability matrix | Complete planning map; expands source section 16 excerpt to all 50 REQ IDs, 15 NOV IDs and 10 NFRs |

**Chunk 0.3 status:** Architecture and traceability documents have been committed. No product architecture components have been implemented by this documentation chunk. The traceability matrix maps all 50 REQ IDs, 15 NOV IDs and 10 NFRs to planned ownership and tests.

**Chunk 0.4 status:** CI passed. Gitleaks and Semgrep passed; both initial CodeQL jobs failed during Analyze; a SARIF-upload permission remediation is committed and its rerun remains pending. The Playwright checks cover the bootstrap shell and design-system component interactions, not full analyst workflows.

**Chunk 1.1 status:** Design tokens and reusable UI primitives plus a dedicated showcase route are committed. No API integration or production telemetry was added. The final CI run must pass before marking the chunk verified.

**Do not infer requirement completion from the presence of the repository scaffold or a passing bootstrap CI run.**


| Frontend landing page (Chunk 1.2) | Implemented: responsive product landing page, CSS-only cinematic atmosphere, product capabilities, T1/T2/T3 visibility explanation, privacy principles and Playwright coverage; final CI verification pending; see docs/reports/chunk_1_2_report.md |

| Frontend dashboard shell (Chunk 1.3) | Implemented: responsive analyst workspace, grouped route navigation, active state, collapsible desktop sidebar, mobile drawer and honest API-disconnected placeholders; CI/security verification pending; see docs/reports/chunk_1_3_report.md |


| Frontend dashboard page templates (Chunk 1.4) | Implemented: Overview, AI Inventory, Leak Alerts, Agent Graph, Compliance, Data Sources, Policy Studio and System & Privacy templates; all example records are synthetic, controls are local previews, and no backend/collector integration is claimed; see docs/reports/chunk_1_4_report.md |


| Backend canonical domain contracts (Chunk 2.1 / M0.2) | Implemented: versioned Pydantic Event, Finding, AITool, Evidence, provenance and collection-coverage contracts; privacy-safe transient body reference and validation tests; see docs/reports/chunk_2_1_report.md. CI verification pending. |


## 7. Current execution update — Chunk 2.2

| Work package | State |
|---|---|
| M0.2 canonical domain contracts (Chunk 2.1) | Implemented; CI and security workflows passed on commit a1a65c3 |
| M0.3 SQLite/SQLModel schema and WAL foundation (Chunk 2.2) | Implemented in backend/app/persistence.py; migration marker, core tables, indexes, foreign keys, session transaction helper and persistence tests added; CI/security passed after follow-up fixes |
| M0 remaining | Bounded event bus, CLI/init/serve, local bearer token, DB-aware health and structured redacted logging remain outstanding |

Chunk 2.2 is a persistence primitive only: it is not yet wired into the FastAPI lifecycle or ingest pipeline. No raw request-body table is defined, and transient body references are excluded from event serialization.


## 7. Current execution update — Chunk 2.3

| Work package | State |
|---|---|
| M0.2 canonical domain contracts (Chunk 2.1) | Implemented; CI and security workflows passed on a1a65c3 |
| M0.3 SQLite/SQLModel schema and WAL foundation (Chunk 2.2) | Implemented; CI/security workflow status tracked on commit aaf0ac1 |
| M0.4 bounded asynchronous event bus (Chunk 2.3) | Implemented: bounded queue, awaitable backpressure, explicit nonblocking rejection, counters, worker isolation/drain and collector supervision with capped restart backoff; CI/security passed on commit 5d0a63d |
| M0.5–M0.6 | Chunks 2.4–2.5 implement local bearer-token auth, protected metadata intake, DB-aware health, structured JSON application logs and redaction tests; CLI work remains outstanding |

Chunk 2.3 does not connect collectors to FastAPI or persistence. Queue capacity and worker count are constructor-configurable; deployment configuration and health/API exposure are later integration work.


## 8. Current execution update — Chunk 2.4

| Work package | State |
|---|---|
| M0.3 SQLite persistence | Integrated into FastAPI application lifespan; initialization is idempotent and database connections are disposed after queue drain |
| M0.4 event bus / collector supervision | Integrated; collectors stop before bus shutdown, and the bus drains accepted work before database disposal |
| M0.5 local bearer token and protected API | Implemented: first-run random token file, owner-only permissions, constant-time comparison, authenticated event intake, docs and OpenAPI |
| M0.5 health and ingestion vertical slice | Implemented: unauthenticated `GET /api/health` checks DB and reports bus/collector status; authenticated `POST /api/events` accepts canonical metadata events |
| M0.6 structured redacted logging | Still outstanding; this chunk does not claim request/log secret-redaction coverage |
| M0 remaining | CLI init/serve is implemented in Chunk 2.6; real collectors, multipart HAR/JSONL/PCAP parsing, normalizer/detectors, SSE, remaining CLI actions and broader API inventory remain outstanding |

Chunk 2.4 deliberately keeps raw bodies out of the HTTP ingestion contract: the request-specific schema has no `body_ref` field, and sensitive HTTP headers are redacted before persistence. Queue acceptance returns `202`, not a durable-commit guarantee; the event bus is in-memory and may lose queued work if the process terminates before persistence completes. No real collector is configured by default.

The API route follows the source's `/api` prefix and `/api/health` NFR-SEC-1 exception. The former bootstrap `/api/v1/health` path is no longer used. Multipart upload support remains assigned to the provider/collector milestone, not this application-wiring chunk.


## 9. Current execution update — Chunk 2.5

| Work package | State |
|---|---|
| M0.6 structured JSON logging | Implemented with structlog, timestamps, severity and JSON rendering to stderr |
| Privacy-safe HTTP access logs | Implemented: route template, method, status, duration and server request ID only; no raw query, headers, client address or body |
| Secret/payload redaction | Implemented recursive sensitive-key redaction, common bearer/API-key pattern scrubbing, bounded strings/collections/depth and no arbitrary object repr |
| Failure diagnostics | Worker/collector logs record exception class and counters/backoff only; collector supervisor retains only exception class |
| Operational hardening | Uvicorn access logging disabled; generic internal-error response; `X-Request-ID` returned for handled responses |
| M0 remaining | CLI init/serve is implemented in Chunk 2.6; real collectors, multipart ingestion, remaining CLI actions, structured file logging/rotation and broader API inventory remain outstanding |

Chunk 2.5 does not claim that third-party, host OS or process-supervisor logs are sanitized. Application-owned logging is covered by focused redaction and no-query/header/body tests. Raw payloads and exception messages are not intentionally logged.


## 10. Current execution update — Chunk 2.6

| Work package | State |
|---|---|
| Typed local runtime settings | Implemented using Pydantic Settings: .env/environment loading, data/token/database paths, port, queue, workers, timeout and log level |
| Loopback default and enforcement | Implemented in the official CLI: localhost and literal loopback addresses only; non-loopback binds are rejected |
| Restricted CORS | Implemented: only local HTTP(S) origins; no wildcard/remote origins or credentials; request ID exposed |
| shadowlens init | Implemented: private local state, random token, SQLite schema and non-enforcing policy starter; idempotent and preserves existing policy files |
| shadowlens serve | Implemented: starts the FastAPI app through Uvicorn with access logging disabled; optional reload for local development |
| Optional adapters | --live and --gateway fail closed because live capture and Lens Gateway are not implemented |
| CLI still pending | scan, ingest, simulate, demo, bench, export and forget remain future implementation work |

The generated policy.default.yaml is intentionally comments-only and does not represent an active or validated policy. Only init and serve are supported commands in this chunk. The official CLI enforces loopback binding; a direct custom Uvicorn invocation can bypass CLI bind validation and must not be treated as the recommended launch method.


## 7. Current execution update — Chunk 3.1 (REQ-DISC-001)

| Work package | State |
|---|---|
| Provider registry | Implemented in `backend/app/providers/providers.yaml`; 25 required cloud, local and developer-tool entries |
| Signature dimensions | Exact/wildcard DNS hosts, URL paths, destination ports, SNI, bounded header fingerprints and User-Agent |
| Classification | Deterministic weighted evidence; host/SNI and independent corroborating signals; safe evidence descriptions |
| Unknown destinations | LLM-like paths or bounded JSON key names `messages`/`prompt` become `unknown_llm_api`, confidence 0.7, provisional; path/shape alone never confirms a named provider |
| Hot reload | YAML schema validation occurs before atomic registry replacement; invalid reload preserves previous registry |
| Privacy | No request body values are accepted; sensitive headers are excluded from Signal repr/serialization and matched values never appear in classification evidence |
| Tests | Positive coverage for all 25 required provider IDs; negative generic/lookalike tests and a per-provider unrelated-host negative test; wildcard, unknown, malformed-registry and privacy-contract tests |
| Dependency/package | PyYAML declared; YAML registry included in installed package data |
| Verification | Pull-request CI pending; do not mark verified until backend tests/lint/typecheck and existing frontend/security workflows complete |

**Chunk scope:** REQ-DISC-001 only. REQ-DISC-002 sanction policy and deduplication, REQ-DISC-003 config scanning, and REQ-DISC-004 browser-extension discovery remain separate chunks.
