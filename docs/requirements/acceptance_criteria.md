# ShadowLens Acceptance Criteria

**Source:** `ShadowLens_Unified_Master_Specification.md`, sections 0–22.  
**Scope:** 50 unique REQ IDs, all source-specified NFR targets, all 10 simulator scenarios.  
**Status convention:** These are acceptance oracles for future implementation, not claims that tests already exist or pass.

## 1. Global acceptance invariants

Every requirement test must respect these specification-wide constraints:

1. No MITM, certificate injection, TLS decryption or claim of passive HTTPS body inspection.
2. Every event/finding carries source and visibility. T1 = observed metadata; T2 = inferred flow shape; T3 = verified content from an authorized plaintext source. DERIVED and UNAVAILABLE are distinct states.
3. Unknown endpoints remain provisional; provider clues such as process name/package name are not proof of active AI use.
4. Raw secrets/prompts are transient only; do not persist them in DB, files, logs, traces, exports or default API responses.
5. Do not inspect shell history, .env values, credential stores or secret values in config discovery. Config scanning is opt-in, read-only and allowlisted.
6. psutil does not provide universal file-read or shell-command auditing. Unsupported sources are shown as unavailable.
7. Entropy is heuristic, not proof. Canary values are synthetic, user-planted and explicitly approved.
8. LLM advice is optional, redacted, schema-validated and advisory only. It cannot create/remove/override deterministic findings or risk scores.
9. Core must run without LLM credentials; deterministic fallback is always available.
10. Simulation uses synthetic data and never executes described shell commands or performs real exfiltration.
11. Compliance mappings are informational, not a certification or legal-compliance claim.
12. Every finding records source, tier, detector/rule version and evidence reference; derived scores identify algorithm/policy version.

## 2. Functional acceptance criteria

### Collection — section 6.1

#### REQ-COL-001 — Socket collector (P0)
**Given** a process connects to `api.anthropic.com:443`, **when** the collector polls the socket table, **then** a T1 socket event appears within 5 seconds with correct process name and available metadata. **And** when another user's process is inaccessible, collection degrades gracefully, logs a warning once, and coverage/dashboard reports partial visibility. Poll interval defaults to 2 seconds and is configurable.

#### REQ-COL-002 — PCAP ingestion (P0)
**Given** a valid PCAP/PCAPNG ≤200 MB containing HTTPS to `api.openai.com` and plaintext POST to `127.0.0.1:11434/api/generate`, **when** ingested, **then** HTTPS produces T1/T2 metadata without body visibility and plaintext local HTTP can produce a T3 content event. TCP flow reassembly, TLS ClientHello SNI/ALPN/JA4-style metadata, DNS and plaintext HTTP/1.1 are parsed. Malformed/truncated input is safely rejected/reported.

#### REQ-COL-003 — HTTP/log ingestion (P0)
**Given** a HAR with 500 entries including 12 AI-provider calls, **when** imported, **then** 12 AI events are identified, bodies are passed to the inspector, and raw bodies are not persisted. Equivalent format detection is tested for mitmproxy JSON export, nginx/squid-style JSONL and ShadowLens mock-log format. The importer validates UTF-8, supported suffix/format, a 25 MiB initial file cap, 10,000-record cap and bounded JSONL lines; malformed records are reported without echoing source data. Imported events are T1 metadata only, sensitive headers are redacted, and request/response bodies are never retained. **Implementation boundary:** this chunk does not yet route transient body bytes to a detector/inspector; that handoff remains pending the detection/inspection pipeline.

#### REQ-COL-004 — Local LLM loopback capture (P0 in section 6)
**Given** Ollama is running and a script calls `/api/chat`, **when** optional loopback capture is enabled with required permission, **then** inspected plaintext reaches the inspector as T3. Detect listeners on 11434, 1234, 8080/8000 and heuristic 5000/7860 ports. Without privilege, fall back to T1 and explain the gateway alternative. No privilege escalation occurs automatically. **Priority conflict:** section 21 lists this as P2.

#### REQ-COL-005 — Lens Gateway (P0 in section 6)
**Given** the user explicitly opts in and points a compatible client to `http://127.0.0.1:8787`, **when** a request containing an AWS key is forwarded, **then** upstream receives the request unmodified in audit-only mode, ShadowLens stores a critical finding with masked evidence, response streaming is preserved, and request bodies are never stored. The specified p95 added latency excluding upstream is <15 ms. Routes cover OpenAI `/v1/*`, Anthropic `/v1/messages`, Ollama `/api/*`. Gateway binds loopback, restricts upstreams and prevents arbitrary URL/SSRF behavior. **Priority conflict:** section 21 lists full gateway compatibility as P2.

#### REQ-COL-006 — Agent hook adapters (P1)
**Given** a supported structured trace source (LangChain/LangGraph, OpenAI Agents/Anthropic JSONL, AutoGPT-style log, MCP JSON-RPC, Cursor/Claude Code log directory), **when** an agent invokes a tool, **then** the adapter emits normalized agent activity with the available tool/argument/time/approval evidence. Explicit example: a LangChain shell tool running `ls ~` produces an `agent_behavior` event. Missing source fields remain unknown, not invented.

#### REQ-COL-007 — Mock/scenario traffic (P0)
**Given** a fresh install without internet, **when** `shadowlens demo` runs, **then** it generates/replays at least 8 synthetic scenarios, fills the dashboard with realistic findings in <20 seconds and can write corresponding mock logs/PCAPs. The full section 14 demo covers S1–S10.

### Shadow AI discovery — section 6.2

#### REQ-DISC-001 — Provider classification (P0)
**Given** each registry entry, **when** its provider tests run, **then** it has at least one positive and one negative test. Cover the providers/tools named in section 6.2. **Given** an unknown host with an LLM-like path (`/v1/chat/completions`) or JSON `messages`/`prompt`, **when** classified, **then** it is marked `unknown_llm_api` with confidence 0.7, not a confirmed known vendor.

#### REQ-DISC-002 — Sanctioned vs shadow (P0)
**Given** policy sanctions only Anthropic and Azure OpenAI, **when** a process calls `api.openai.com`, **then** create one medium `shadow_ai` finding for the (host, process, provider) tuple and deduplicate repeats for 24 hours.

#### REQ-DISC-003 — Config-based discovery (P0 in section 6)
**Given** an allowlisted MCP config contains `command: npx @modelcontextprotocol/server-filesystem /`, **when** the user opts in to read-only discovery, **then** an `ai_tools` record identifies an MCP server with `fs:read/write root=/` capability and a high root-scope finding. Inspect only known AI-related keys/metadata from editor manifests, MCP config, Ollama model listing, global package names, process names and AI environment-variable names; never read .env values, shell history or credential stores. **Priority conflict:** section 21 lists this feature as P1.

#### REQ-DISC-004 — Browser-extension AI detection (P1)
**Given** a read-only browser extension manifest requesting `https://api.openai.com/*`, `<all_urls>` and `clipboardRead`, **when** matched against the provider registry, **then** produce a high-severity "AI extension with broad data access" finding with manifest/permission evidence.

### Payload detection — section 6.3

#### REQ-DET-001 — Detection pipeline (P0)
**Given** decoded payload text with provider/tool/tier context, **when** inspection runs, **then** it extracts JSON strings, unescapes and recursively decodes base64/URL/gzip to depth ≤3 and ≤5 MB, extracts regex/entropy candidates, validates them, applies context and placeholder scoring, fuses confidence and emits findings according to section 8.2. p95 latency: ≤30 ms for ≤64 KB and ≤400 ms for 1 MB.

#### REQ-DET-002 — Secret rule set (P0)
**Given** positive/negative fixtures for each required secret family, **when** rule tests run, **then** AWS access/secret, GitHub PAT, OpenAI, Anthropic, HF, Google API, Slack, Stripe, JWT, private-key, DB URL, Basic-auth URL, Bearer and generic entropy detections match their specified patterns, validators, severity and placeholder exclusions. Pairing AWS access key with nearby 40-character secret upgrades to critical; JWT parsing checks JSON header/payload, `typ`, `exp`, and flags `alg=none`.

#### REQ-DET-003 — Entropy engine (P0)
**Given** the labelled benchmark corpus, **when** entropy and combined detection run, **then** entropy-only false-positive rate is ≤3% and combined secret recall is ≥95%. Charset-normalized thresholds are hex ≥0.75/length ≥32 and base64 ≥0.85/length ≥24. Natural language, common identifiers, UUIDs, Git SHAs (unless near secret context) and lockfile hashes are rejected as specified.

#### REQ-DET-004 — PII rules (P0)
**Given** India/global PII fixtures and near misses, **when** inspection runs, **then** apply RFC-lite email checks, E.164/India phone checks, Luhn + IIN for card numbers, Verhoeff for Aadhaar, PAN fourth-character validation, US SSN area/group rules, IBAN mod-97, internal-IP/hostname recognition, context-gated DOB/name and ≥25-item bulk-PII escalation to critical.

#### REQ-DET-005 — Proprietary/internal data (P0)
**Given** a 200-line Java file sent to a shadow provider with `// Copyright Acme Corp. Internal` and `corp.acme.local` URLs, **when** analyzed, **then** produce high `DATA-PROPRIETARY-CODE` evidence containing counts and masked markers, not source code. Detection includes ≥40-line source-code heuristics, organization headers, configured internal domains/repositories, path markers and confidentiality labels.

#### REQ-DET-006 — Canary detection (P0)
**Given** a user-approved, synthetic planted canary whose HMAC appears in an authorized inspected source, **when** checked, **then** detector checks canaries first and emits critical category `canary`, confidence 1.0, with safe planted-path evidence.

#### REQ-DET-007 — Deduplication/suppression (P0)
**Given** repeated occurrences of identical (HMAC, provider, process) within 1 hour, **when** findings are generated, **then** a single finding increments `occurrences`. **Given** a user marks a false positive, **then** matching rule + context fingerprint is suppressed without broad ungrounded suppression.

#### REQ-DET-008 — Chunked/streaming detection (P1)
**Given** a secret split across adjacent body chunks, **when** the stream is inspected, **then** the sliding window overlap equal to the maximum secret length detects the complete value without persisting raw chunks.

### Agent behavior — section 6.4

#### REQ-AGT-001 — Tool-call extraction (P0)
**Given** OpenAI `tool_calls`, Anthropic `tool_use`, Ollama tool calls, MCP `tools/call` or LangChain traces, **when** ingested, **then** normalize to `{tool, args, approved_by_human: bool|unknown, ts}` while retaining source provenance.

#### REQ-AGT-002 — Shell-command rules (P0)
**Given** structured shell/exec tool-call arguments, **when** tokenized with shell-aware parsing, **then** split and assess chained segments; classify execution, destructive operations, remote execution, privilege escalation, exfiltration, persistence and credential harvesting with the severity levels in section 6.4. No shell command is executed by detection or simulation.

#### REQ-AGT-003 — Filesystem rules (P0)
**Given** a file-read tool call `read_file("../../../home/dev/.ssh/id_rsa")` from project `/work/app`, **when** canonicalized, **then** emit critical `AGT-FS-SENSITIVE-READ` with `outside_root=true`. Cover project-root/allow-list boundaries, unapproved sensitive reads, traversal, symlinks, tilde, environment expansion, Windows short names and `\\?\` prefixes.

#### REQ-AGT-004 — Network rules (P0)
**Given** structured agent network activity, **when** the destination is first-seen, a raw IP, paste/webhook/tunnel sink, or large POST shortly after sensitive read, **then** emit appropriately evidenced network-risk findings. Missing network source data remains unavailable.

#### REQ-AGT-005 — Autonomy (P0)
**Given** a tool instance's observed/structured activity and approval context, **when** autonomy is calculated, **then** classify A0 chat, A1 file reads, A2 file writes, A3 command execution, A4 command + network + no human approval observed. Unknown approval is not silently converted to approved.

#### REQ-AGT-006 — MCP risk (P1)
**Given** MCP server metadata, **when** risk is assessed, **then** score capability breadth, root scope, stdio vs remote SSE transport, pinned vs `@latest` package and unknown publisher; expose the evidence behind each factor.

#### REQ-AGT-007 — Injection-to-exfil chain (P0)
**Given** a tool result with instruction-like indicators followed within 120 seconds by sensitive read or outbound request to a host first seen <10 minutes ago, **when** correlation runs, **then** emit critical `CHAIN-INJECTION-EXFIL` with ordered evidence timeline. Missing stages do not get invented.

### Flow shape — section 6.5

#### REQ-SHP-001 — T2 encrypted-flow analysis (P1)
**Given** encrypted AI-provider flows with process/provider baselines, **when** flow analysis runs, **then** detect: single request >P99 and >256 KB (`SHAPE-BULK-UPLOAD`); ≥20 similarly sized sequential requests within 5 minutes (`SHAPE-CHUNKED-REPO-DUMP`); and regular small-request/large-streamed-response cadence with sub-minute RTT (`SHAPE-AGENT-LOOP`). All findings remain T2 with confidence ≤0.7.

### Risk/compliance/triage — section 6.6

#### REQ-RSK-001 — Risk engine (P0)
**Given** identical findings, evidence, visibility, data classes, provider exposure and autonomy with the same rule/policy versions, **when** risk is calculated, **then** endpoint/tool/provider/org scores are deterministic and bounded 0–100 using section 8.1 severity/tier/data-class/provider/autonomy factors, noisy-OR aggregation and specified time decay/org aggregation.

#### REQ-RSK-002 — Risk explanation (P0)
**Given** a scored scope, **when** `GET /api/risk/{scope}/{id}/explain` is called, **then** return factor contributions, top five drivers and quick-win actions with projected score deltas. No unexplained score-only response.

#### REQ-CMP-001 — Compliance controls (P0)
**Given** versioned rule-to-control mappings in `controls.yaml`, **when** findings are mapped, **then** show framework posture/control coverage and export HTML/PDF reports; identify framework/version/rationale/evidence/limitations. Never claim certification or legal compliance.

#### REQ-CMP-002 — AI-BOM (P1)
**Given** discovered AI components, **when** BOM export is requested, **then** produce CycloneDX 1.6 JSON with machine-learning-model, service and application components and dependency relationships.

#### REQ-TRI-001 — LLM triage (P0 in section 6)
**Given** no API key/network, **when** triage is requested, **then** return deterministic per-rule template remediation and show "Rule-based advice". **Given** Featherless/Ollama is configured, **when** a medium-or-higher finding is triaged, **then** asynchronously return verdict/remediation with p95 <8 seconds. Only redacted minimum context is sent. **Priority conflict:** section 21 lists Featherless advisory triage as P1.

#### REQ-TRI-002 — Triage guardrails (P1)
**Given** malformed/invalid LLM JSON or an LLM disagreement with a VERIFIED canary/checksum-validated finding, **when** triage completes, **then** schema validation rejects the invalid output and deterministic finding wins; disagreement is logged. LLM cannot modify finding status/severity/risk.

### Policy — section 6.7

#### REQ-POL-001 — Policy validation and hot reload (P0)
**Given** a policy YAML following section 7.4, **when** loaded or changed, **then** Pydantic validation accepts valid policy and rejects malformed/schema-invalid policy; valid updates hot-reload without unsafe partial state.

#### REQ-POL-002 — Policy simulation (P1)
**Given** stored events/findings and a candidate policy, **when** `POST /api/policy/simulate` runs, **then** return new/removed violations and score delta without mutating active policy or production records.

### Dashboard — section 6.8

#### REQ-UI-001 — Overview (P0)
**Given** actual persisted service data, **when** overview is loaded, **then** display risk/trend, sanctioned vs shadow tools, critical findings, 24h/7d exfil events, tier mix, top providers/processes and live SSE feed. API errors/empty data must not be replaced with fabricated production metrics.

#### REQ-UI-002 — Inventory (P0)
**Given** discovered tools, **when** inventory page loads, **then** list tool/kind/provider/hosts/first-last seen/sanction/autonomy/risk; selecting a row opens its timeline drawer.

#### REQ-UI-003 — Leak alerts (P0)
**Given** persisted findings, **when** alert filters are applied, **then** filter severity/category/tier/status and show masked evidence, rule, why flagged, confidence, mapped controls, triage and working accept-risk/false-positive/resolve/canary-exclusion actions.

#### REQ-UI-004 — Permission graph (P0 in section 6)
**Given** graph nodes/edges backed by observed or explicitly inferred evidence, **when** the graph opens, **then** React Flow displays process, agent, MCP server, file scope and network host; risk-coloured edges open capability evidence. Inferred edges must not be presented as observed. **Priority conflict:** section 21 lists the graph as P1.

#### REQ-UI-005 — Compliance page (P0)
**Given** compliance mapping results, **when** the page opens, **then** show per-framework posture bars, control table and functioning export actions with informational-not-certification wording.

#### REQ-UI-006 — Ingest page (P0)
**Given** a supported local input file or chosen optional capability, **when** the user uses the page, **then** PCAP/HAR/log drag-drop, live-capture toggle, gateway setup snippets, scenario launcher and canary generator have real, safe behavior or are disabled with a clear permission/availability explanation.

#### REQ-UI-007 — Policy Studio (P1)
**Given** a candidate YAML policy, **when** it is edited/validated/simulated, **then** show schema errors, simulation diff and versions without altering active data until explicitly applied.

#### REQ-UI-008 — Privacy badge (P0)
**Given** the app is running, **when** any route is shown, **then** header visibly states local-only mode, zero raw payloads stored and current LLM triage mode (off/local/remote-redacted); labels reflect actual runtime state.

#### REQ-UI-009 — Accessibility/UX (P0)
**Given** keyboard-only navigation and supported viewport/theme settings, **when** dashboard routes are used, **then** controls are keyboard reachable, contrast meets WCAG AA, dark/light themes work and empty states offer Run Demo CTA.

### Privacy — section 9.1

#### REQ-PRIV-001 — Transient raw-payload lifecycle (mandatory)
**Given** any supported inspection path and a known test secret, **when** the event is processed, **then** raw payload is used only in bounded transient inspection memory and the full secret is absent from database, disk, logs, traces, exports and default API responses. References are released after inspection; no guaranteed memory-zeroization claim is made.

#### REQ-PRIV-002 — Secret HMAC vault (mandatory)
**Given** a detected secret and install salt, **when** retained for deduplication, **then** store HMAC-SHA256 plus masked preview (first 4/last 2 characters) and never store the raw secret.

#### REQ-PRIV-003 — Redacted context (mandatory)
**Given** evidence context around a detected sensitive span, **when** stored or shown, **then** redact every detected sensitive span in the ±40-character snippet to typed placeholders such as `[AWS_KEY]` or `[EMAIL]`.

#### REQ-PRIV-004 — Default redaction/no telemetry (mandatory)
**Given** dashboard/API/export behavior with triage disabled, **when** the app operates, **then** content is redacted by default and no telemetry/external request occurs. External requests only occur after triage is explicitly enabled.

#### REQ-PRIV-005 — Forget (mandatory)
**Given** user invokes `shadowlens forget`, **when** the wipe completes, **then** database, vault and install salt are irreversibly removed. The UI/CLI must not report completion unless all targets were successfully removed.

#### REQ-PRIV-006 — Identifier minimization (mandatory)
**Given** an export without `--include-identifiers`, **when** generated, **then** hostnames and usernames are hashed. The explicit option is the only source-specified opt-in to include them.

## 3. Non-functional acceptance gates — section 10 and 12

| NFR | Acceptance gate |
|---|---|
| NFR-PERF-1 | Benchmark sustained pipeline throughput ≥2,000 events/s on documented 4-core laptop; exclude LLM triage; record fixture size/hardware/method. |
| NFR-PERF-2 | PCAP benchmark ≥50 MB/s and enforce ≤200 MB input cap. |
| NFR-PERF-3 | With live collectors idle, measure <150 MB RAM and <3% CPU. |
| NFR-PERF-4 | Local dashboard first paint <1.5 seconds. |
| NFR-REL-1 | Fault-inject one collector crash; others continue and supervisor restarts failed collector with backoff. |
| NFR-REL-2 | Verify SQLite WAL, ≥500-row batched insert path and automatic retention purge. |
| NFR-SEC-1 | All API routes require bearer auth except `/api/health`; tests include unauthorized request on each protected route. |
| NFR-PORT-1 | Validate Linux full support; macOS psutil limitations; Windows T1/log ingestion and Npcap requirement for loopback sniff. |
| NFR-TEST-1 | Coverage ≥90% on `core/detect`, ≥80% overall. |
| NFR-DOC-1 | Clean-checkout quick-start takes fewer than 5 commands. |

### Detection benchmark — section 12
The simulator-built corpus must contain ≥1,000 labelled samples: 300 positive secrets; 200 positive PII; 200 PII near-miss negatives; 200 hard negatives; 100 agent tool-call traces (50 malicious/50 benign). CI gates: secrets recall ≥95%, precision ≥90%; PII precision ≥95% with checksum backing; agent-rule recall ≥90%, false-positive rate ≤5%. The benchmark prints per-rule table and writes `bench/report.md`.

### Property testing — sections 12–13
- Arbitrary bytes never crash detector.
- Masked evidence never contains the full secret.
- Redaction is idempotent.
- Decode depth is always bounded.
- Parsers and payload processors are fuzzed with Hypothesis.

## 4. Scenario-level acceptance — section 14

| Scenario | Required result |
|---|---|
| S1 | Two critical secret findings (AWS + Stripe), shadow provider, T3 evidence. |
| S2 | Critical PII-BULK with validated Aadhaar. |
| S3 | Critical sensitive file read outside project root; agent autonomy A3+. |
| S4 | Remote shell execution + new-host network findings. |
| S5 | Critical injection-to-exfil finding with ordered event timeline. |
| S6 | High-risk LAN-exposed Ollama, T1 + T3 where plaintext is authorized/available. |
| S7 | T2 chunked-repository-dump finding at confidence ≤0.7, no content claim. |
| S8 | Critical canary match at confidence 1.0 with planted path. |
| S9 | High MCP root-scope/@latest risk, graph shows broad reach. |
| S10 | Sanctioned Azure OpenAI usage counted; no alert. |

The end-to-end demo must replay S1–S10 in approximately 20 seconds offline using synthetic fixtures.

## 5. Phase exit acceptance — section 20

- **Phase A:** clean local start; health reports DB/adapter status; fixture event traverses ingestion → normalization → SQLite; known raw test secret absent from logs/DB.
- **Phase B:** provider positive/negative tests pass; local model endpoints identified from configured indicators; unknown endpoints stay provisional; permission failures visible and do not crash collectors.
- **Phase C:** positive/negative tests for every rule; reproducible secret/PII results; full matched values absent from persisted data/logs/API/exports; per-detector benchmark report.
- **Phase D:** supported fixtures generate expected findings; simulator does not execute shell commands; every finding links originating audit event(s); unsupported sources shown unavailable.
- **Phase E:** same events + same policy version yield same score; score explanation in API/UI; policy simulation does not mutate live state; framework mappings versioned/informational.
- **Phase F:** every graph node/edge links to real evidence; filters/status work; replay read-only; empty/error/partial-permission/no-Featherless states usable.
- **Phase G:** core works with LLM off; advisor receives redacted context only; gateway loopback/upstream restricted; offline synthetic end-to-end demo reproducible.

## 6. Definition of Done — section 22

Release acceptance requires all P0 requirements to have IDs, implementation and passing tests; every finding source/tier/rule version/evidence; no encrypted-content overclaim; unknown endpoints provisional; OS coverage visible; raw secrets/prompts not persisted by default; LLM isolation; reproducible risk; safe upload validation/cleanup; safe synthetic simulator; API-backed dashboard actions; no-key core operation; reproducible clean install/demo; and README platform/permission/limitation/privacy documentation.


### Implementation notes — Chunk 3.1 (REQ-DISC-001)
- The registry is loaded from `backend/app/providers/providers.yaml` and can be atomically reloaded after full schema validation.
- Classification consumes destination host, URL path, port, SNI, bounded headers, User-Agent and optional JSON top-level key names from an upstream bounded parser. It never consumes or retains body values.
- Exact and wildcard DNS-label matching is boundary-aware; path/port-only clues cannot confirm a provider.
- Unknown LLM-like request paths or JSON key shapes return `unknown_llm_api`, confidence `0.7`, and `provisional=true`.
- Provider match evidence records signal types and safe descriptions only; secret-bearing header values are not copied into classification results.
