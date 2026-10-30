# Chunk 0.3 — Architecture and Traceability Report

**Project:** ShadowLens  
**Repository:** `parthiv-doraswamy/ShadowLens`  
**Branch audited:** `main`  
**Scope:** Architecture and requirement traceability only. No product code was implemented by this chunk.

## 1. Outcome

<badge>Complete</badge>

The required architecture baseline and traceability matrix were present in the repository at the start of this execution. They were audited against the complete root master specification and the Chunk 0.2 requirement catalog. The documents cover the requested architecture views and satisfy the planning-level traceability checks; no duplicate replacement documents were created.

## 2. Architecture artifacts audited

| File | Scope verified |
|---|---|
| `docs/architecture/system_architecture.md` | Local-first modular monolith, runtime topology, boundaries, dependencies, ADRs and non-goals |
| `docs/architecture/backend_architecture.md` | Python/FastAPI package boundaries, layering, pipeline lifecycle, API ownership, failure handling and security controls |
| `docs/architecture/frontend_architecture.md` | React/TypeScript responsibility, route ownership, shared UI modules, state/API boundaries and accessibility |
| `docs/architecture/event_pipeline.md` | Replaceable collectors, canonical event flow, queue/backpressure, transient payload lifecycle, evidence links and replay |
| `docs/architecture/data_model.md` | Canonical Event/Finding, visibility types, persistence entities, API DTOs, lifecycle and schema evolution |
| `docs/architecture/privacy_boundary.md` | Data classes, retention/redaction, external network boundary, config discovery, visibility honesty and user controls |
| `docs/architecture/threat_model.md` | Assets/trust boundaries, STRIDE-lite threats, mitigations, assumptions, limitations and security test families |

The architecture consistently specifies a local-first modular monolith; loopback defaults; SQLite WAL; bounded asynchronous processing; deterministic inspection before optional advisory triage; replaceable source adapters; and strict separation between domain logic, persistence, API and UI.

## 3. Traceability validation

Audited `docs/requirements/traceability_matrix.md` against `docs/requirements/requirements_catalog.md`.

| Check | Actual result |
|---|---:|
| Unique REQ IDs in catalog | 50 |
| Primary REQ rows in matrix | 50 |
| Missing REQ rows | 0 |
| Duplicate primary REQ rows | 0 |
| Primary rows with module/chunk/test/outcome fields | 50 |
| NOV features mapped | 15 / 15 |
| NFRs mapped to verification | 10 / 10 |

Every REQ row identifies a primary module, planned chunk/milestone, planned test path and observable outcome. Test paths are plans only; their existence or execution is not claimed.

## 4. Contract and safety checks

The audited documents preserve these source constraints:

- No TLS interception/decryption or claim of passive HTTPS body inspection.
- T1 metadata, T2 inferred flow shape and T3 authorized plaintext remain distinct; DERIVED and UNAVAILABLE are separate evidence states.
- Raw payloads are transient only; persisted evidence is masked, HMAC-based and redacted.
- Unknown endpoints remain provisional until corroborated.
- psutil is not represented as universal file-read or shell-command auditing.
- Config scanning, canary placement, live loopback capture, Lens Gateway, LLM triage and deployment remain opt-in/permission-gated.
- LLM triage is advisory and cannot override deterministic findings or risk.
- Simulator replay is synthetic and must not execute shell commands or perform real exfiltration.
- Compliance mappings are informational, not certification.

The backend architecture explicitly records the current bootstrap route `/api/v1/health` versus the specification's `/api/health` and the NFR-SEC-1 exception. This remains an M0 implementation decision/test, not an undocumented assumption.

## 5. Limitations and unresolved decisions

- The master specification's priority conflicts remain recorded in the requirements catalog; this architecture audit does not resolve them.
- Queue capacity, worker concurrency, overflow policy and shutdown-drain behavior remain implementation decisions to document and test before the Phase A exit gate.
- Exact client-side route URLs remain for UI implementation; API route ownership is mapped.
- Platform permissions and OS-specific telemetry coverage require validation on the selected target machine.
- Architecture and traceability documents do not prove any REQ is implemented. Product requirements remain unverified until their tests exist and pass.

## 6. Commands/checks performed

Repository/API inspection performed through the connected GitHub repository:
- Read the root master specification architecture/domain model section (section 4–5).
- Read the source privacy/threat model section (section 9).
- Read the source NFR, traceability, milestone and phase-gate sections.
- Fetched and inspected all seven architecture documents and the traceability matrix.
- Compared unique REQ IDs in the catalog with primary traceability rows.
- Checked each primary row has planned test ownership and outcome fields.

No local test suite was run by this documentation audit. No test result is inferred from the earlier Chunk 0.2 CI run.

## 7. Next chunk

Proceed to **Chunk 0.4 — CI/security automation**. Keep architecture and frontend/backend feature branches separate until canonical contracts stabilize. Add security scanners only with real configuration; do not claim a scanner is active merely because its workflow file exists.
