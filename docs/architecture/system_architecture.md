# ShadowLens System Architecture

**Status:** Architecture baseline for Chunk 0.3; design only, no product code implemented.  
**Source:** Unified Master Specification sections 0–5, 7, 9–11, 15–17 and 20–22.

## 1. Architectural decision

Build a **local-first modular monolith** in one Python application process, with a separate React analyst UI. Do not introduce microservices. Keep module boundaries explicit so collectors, detection engines and integrations can be replaced independently.

The application binds to loopback by default. SQLite WAL is the local persistence layer. Core operation must not depend on a cloud service or LLM credentials.

## 2. Context and runtime boundaries

- **Local machine / operator:** owns the host being audited and explicitly enables optional data sources.
- **Collectors:** obtain socket/process metadata, offline PCAP, HAR/JSONL/proxy logs, structured agent events and opt-in configuration metadata.
- **Core pipeline:** canonicalizes input, classifies providers, runs deterministic detectors, analyzes agent behavior, correlates evidence and calculates risk.
- **Local persistence:** SQLite WAL stores normalized metadata, findings, HMAC fingerprints, policies and risk snapshots; raw payloads are transient only.
- **API:** FastAPI exposes authenticated REST endpoints and SSE updates.
- **Dashboard:** React/TypeScript/Vite calls the local API and displays evidence, visibility and coverage limitations.
- **Optional advisor:** Featherless or local Ollama receives redacted context only after deterministic analysis. It is not a source of truth.
- **Optional integrations:** Lens Gateway and live loopback capture remain explicitly opt-in and permission-gated.

## 3. Logical component map

| Component | Responsibility | Must not do |
|---|---|---|
| Collector adapters | Acquire source-specific observations and emit canonical events | Decide severity, risk or policy |
| Normalizer | Validate, normalize, bound decoding and preserve provenance | Persist raw request bodies |
| Provider classifier | Match registry signals and classify known/unknown providers | Treat process/package clue as proof |
| Payload inspector | Run deterministic secret, PII, proprietary-data and canary rules | Send raw data to LLM |
| Agent analyzer | Normalize tool calls and evaluate shell/filesystem/network behavior | Claim OS-wide audit coverage from psutil |
| Flow-shape analyzer | Infer upload/cadence patterns from metadata | Claim content visibility |
| Correlator | Link events/findings into ordered chains | Invent missing evidence stages |
| Risk engine | Compute reproducible bounded scores and explanations | Accept LLM score overrides |
| Compliance mapper | Map rule IDs to versioned informational controls | Claim certification |
| Triage advisor | Offer optional advisory remediation from redacted context | Create/delete/override deterministic findings |
| Repositories | Persist canonical metadata and evidence references | Persist raw payloads |
| API | Authenticate, validate, expose service operations and stream updates | Bypass service/privacy boundaries |
| Frontend | Render API-backed state and operator actions | Show fabricated production metrics |

## 4. Runtime topology

One backend process hosts FastAPI, collector supervision, bounded asynchronous workers, domain services and repositories. The React development/build output is a separate client. SQLite is local. Optional network egress is limited to explicitly enabled advisory triage or configured upstream forwarding through the opt-in gateway.

No collector or integration is allowed to silently widen the network or permission boundary.

## 5. Dependency direction

- Collectors depend on canonical contracts and source-specific parsing helpers.
- Normalization/classification/detection/agent/shape/correlation modules depend on domain contracts, not FastAPI or UI.
- Risk and compliance consume findings and policy/control definitions.
- Application services orchestrate domain modules and repositories.
- API routers depend on application services and auth.
- Frontend depends on typed API contracts, never on backend internals.
- Optional LLM adapter depends on a narrow triage interface and redacted DTO.
- Repositories implement persistence interfaces; domain rules do not issue SQL.

## 6. Cross-cutting contracts

- Every event preserves source, timestamp, host/process attribution when available, and visibility.
- Every finding records rule/detector version, source tier, evidence references and confidence.
- T1/T2/T3 are distinct from DERIVED and UNAVAILABLE states.
- Unknown endpoints remain provisional until corroborated.
- Uploads are untrusted, bounded and cleaned up.
- Raw payloads stay transient; stored evidence is masked/redacted.
- Collector failures are isolated and visible.
- Deterministic findings and risk are reproducible.

## 7. Delivery boundaries

The master plan's phases A–G and milestones M0–M8 remain the delivery authority. This architecture does not promote advanced capabilities into MVP merely because an interface is reserved for them. Priority conflicts are recorded in the requirements catalog and must be decided before scheduling the conflicting work.

## 8. Architecture decisions

| ID | Decision | Rationale / consequence |
|---|---|---|
| ADR-001 | Modular monolith | Matches master spec; simple local install and one canonical pipeline |
| ADR-002 | Canonical event boundary | Replaceable collectors and consistent downstream processing |
| ADR-003 | Deterministic detection first | Explainability, testability and no LLM authority |
| ADR-004 | SQLite WAL local persistence | Local-first and operationally simple |
| ADR-005 | Loopback by default | Minimize exposure of local security data |
| ADR-006 | Transient raw payloads | Privacy requirement; no raw-body database model |
| ADR-007 | Optional integrations behind ports | Core works without credentials or privileged capture |
| ADR-008 | Evidence and visibility first | Prevent overclaiming encrypted or unavailable telemetry |

## 9. Out of scope

No microservices, mandatory kernel driver, TLS interception, cloud dependency, automatic privilege escalation, broad file-content crawling, or LLM-controlled enforcement.
