# ShadowLens Human Approval & Permission Gates

**Source:** `ShadowLens_Unified_Master_Specification.md`, sections 1, 3, 6, 9, 10, 17, 19–22; implementation gates from the work-allocation plan.  
**Purpose:** Identify actions that must remain opt-in, require a user decision, need machine permissions, or must not be activated automatically.

## 1. Non-negotiable defaults

- Bind API/dashboard and optional gateway to `127.0.0.1` by default. Do not expose to LAN by default.
- Generate a random bearer token on first run; use restrictive CORS, CSP and file permissions.
- No MITM, certificate injection, SSL/TLS decryption, or claim of encrypted payload visibility.
- No mandatory kernel driver or enterprise-wide agent.
- Do not elevate privileges automatically.
- Config scanning is opt-in, read-only and metadata-minimized.
- Do not read shell history, `.env` values, credential stores or secret contents for config discovery.
- No raw secret/prompt persistence by default.
- Remote LLM triage is disabled unless explicitly enabled; send redacted minimum context only.
- Simulator uses synthetic fixtures and never executes commands or performs real exfiltration.
- Public demos, if approved, use synthetic data only, with no live collectors or real user evidence.
- Unsupported sources/capabilities remain disabled or unavailable and are reported honestly.

## 2. Explicit user decision / opt-in gates

| Gate | Decision or approval | Required before | Safe default / implementation boundary | Source |
|---|---|---|---|---|
| HAG-01 Demo OS target | Confirm target OS for actual device validation. | Cross-platform validation and M0/M8 platform sign-off. | Do not claim all platforms tested. Report Linux/macOS/Windows support and psutil/Npcap constraints separately. | §10, §19 open question (a), §17 M0/M8 |
| HAG-02 Internal domains/sample policy | Supply or approve organization-specific internal domains and example policy values. | Accurate proprietary/internal-domain detection and policy demo. | Use clearly labelled synthetic demo domains until supplied; never guess real organization domains. | §6.3 REQ-DET-005, §7.4, §19 open question (d) |
| HAG-03 Config discovery opt-in | User explicitly enables read-only discovery and chooses supported scan scope. | Running NOV-2 / REQ-DISC-003 scanner. | Disabled by default; only AI-related allowlisted keys/metadata; environment variable names only (values hashed); never inspect shell history, .env values or credential stores. | §3 NOV-2, §6.2 REQ-DISC-003, §9.1 |
| HAG-04 Canary placement approval | User selects the target test directory and approves planting synthetic canary values. | Creating/planting canaries. | Never silently plant; identify synthetic values as test data; support cleanup. | Global prompt, §3 NOV-4, §6.3 REQ-DET-006 |
| HAG-05 Live loopback capture permission | User explicitly enables optional loopback sniffing and grants OS permission where required. | Scapy loopback capture / T3 from local plaintext. | Off by default; no auto elevation; if permission is absent, fall back to T1 and explain the limitation/gateway alternative. | §2, §6.1 REQ-COL-004, §10 |
| HAG-06 Lens Gateway opt-in | User explicitly chooses to enable/configure gateway and point a client at it. | Starting gateway or changing client base URLs. | Disabled by default; loopback-only; upstream allowlist; SSRF controls; audit-only default; no body persistence; never TLS MITM. | §6.1 REQ-COL-005, §9.2, §19 open question (c) |
| HAG-07 Remote LLM triage | User enables remote triage and supplies/authorizes provider credentials/model choice. | Sending any advisory request to Featherless. | Off by default; no external request absent explicit setting; redact to rule/category/masked evidence/context/provider/tool/tier/autonomy only; deterministic fallback. | §2, §6.6 REQ-TRI-001, §9.3, §19 open question (b) |
| HAG-08 Local Ollama triage | User configures/enables local Ollama advisory endpoint. | Sending local triage requests. | Optional; core features remain functional without it; configured endpoint must be loopback by default unless explicitly secured/configured. | §2, §9.3 |
| HAG-09 Public deployment/demo | User explicitly approves any public deployment and hosting provider/exposure. | Publishing a public demo or deployed app. | No public deployment by default. Synthetic data only; no live collectors, real evidence or secrets. Document env vars, access, retention and rollback. | Work-allocation plan §9.5; section 22 |
| HAG-10 Optional OS telemetry adapters | User explicitly approves installation/enabling of a platform-specific adapter and its permission model. | macOS Endpoint Security, Linux auditd/eBPF, optional Scapy capture or equivalent. | Capability-detect; least privilege; start/stop controls; no bypass of OS controls; unsupported adapters disabled and documented. | Work-allocation plan §9.3; §1 non-goals; §10 |
| HAG-11 Windows packet capture dependency | User/admin installs and configures Npcap if Windows loopback capture is selected. | Windows loopback sniffing. | T1 + log ingestion remain available without Npcap; do not imply loopback sniff support without it. | §10 NFR-PORT-1 |
| HAG-12 Broader process visibility | User/admin decides whether to grant required OS permissions for other users' process/socket metadata. | Collecting beyond current user's visible sockets/processes. | Do not request elevation automatically; show partial visibility and continue unprivileged. | §6.1 REQ-COL-001; §10 platform caveats |
| HAG-13 Gateway shipping scope | User/product owner decides whether gateway is included in first public demo. | Committing to M6 gateway deliverable. | Defer safely if opt-in, allowlist, SSRF, loopback and non-persistence requirements cannot be proven. | §19 open question (c); priority conflict catalog |
| HAG-14 Compliance framework versions | Product owner confirms versions/scope of frameworks to display and review mappings. | Publishing framework-specific control posture as more than an informational reference. | Informational only; record framework version/rationale/evidence/limitations; never claim certification/legal compliance. | §3 NOV-8; §6.6 REQ-CMP-001; global safeguards |
| HAG-15 Irreversible forget operation | User intentionally invokes the forget-all action. | Deleting database, vault and salt. | The source defines irreversible wipe. Confirmation UX and recovery wording are not specified; treat the confirmation design as an open product decision and never report success before the wipe is verified. | §3 NOV-11; §6.9 CLI; §9.1 REQ-PRIV-005 |
| HAG-16 File/log/PCAP ingestion | User selects and submits input data to ingest. | Processing local HAR/JSONL/PCAP/proxy exports. | Treat all inputs as untrusted: strict size limits, safe parsing, bounded resources, temp-file cleanup, transient body handling and redaction before persistence. | §6.1 REQ-COL-002/003; §9.2 |
| HAG-17 Model/provider selection | User confirms Featherless model or local model choice and credentials if LLM triage is desired. | Activating optional LLM triage. | Model names must be checked against provider availability at build/activation time; no credentials are required for core operation. | §2 stack decisions; §9.3; §19 open question (b) |

## 3. Permission and data-source matrix

| Capability/source | Permission model | Data boundary | Failure behavior |
|---|---|---|---|
| psutil socket/process metadata | Current-user visibility by default; broader access may require OS permissions. | PID/process metadata, socket endpoints and supported fields only. | Catch permission/race errors; warn once; report partial visibility; other collectors continue. |
| Offline PCAP | User selects file; no live capture permission needed to parse existing capture. | Metadata and authorized plaintext present in capture; never decrypt TLS. | Size/type validation, safe parser limits, malformed input errors. |
| Live loopback capture | Optional Scapy; platform-specific privilege may be required. | Local plaintext only when actually visible/authorized. | T1 fallback and explanation when unavailable. |
| HAR/JSONL/proxy logs | User provides export/source. | Inspect payload transiently; redact before any retained evidence. | Reject malformed/oversized data; no raw body persistence. |
| Lens Gateway | Explicit client configuration and opt-in. | Plaintext received because client voluntarily targets local proxy; upstream restricted. | Disabled by default; no arbitrary URL forwarding; no body storage. |
| Config scanner | Explicit read-only opt-in. | Allowlisted AI-relevant metadata/config keys only; never secret values. | Skip unsupported paths; show coverage and source. |
| Agent hooks | User installs/configures callback or provides supported trace. | Structured tool/session events that the source actually supplies. | Missing provenance/approval/action data stays unknown/unavailable. |
| LLM triage | Explicit local/remote mode; remote provider key when used. | Redacted minimum context only; strict JSON output. | Timeout/rate limit/cache; deterministic remediation fallback. |
| Simulator | No external permission. | Synthetic labeled events, logs and PCAP. | Never run commands or perform real network exfiltration. |
| Public demo | Explicit deployment approval. | Synthetic demo data only; no live collector or real user evidence. | Do not deploy if access/retention/privacy/rollback settings are unclear. |

## 4. Open decisions copied from section 19

These remain user/product-owner decisions, not implementation assumptions:

1. Target OS for the demo machine.
2. Featherless model choice and key availability.
3. Whether Lens Gateway ships in the first demo.
4. Organization-specific internal domains for the sample policy.

## 5. Approval-record template

Record each decision in project documentation before enabling the capability:

| Field | Value |
|---|---|
| Gate ID | HAG-__ |
| Decision | APPROVED / DEFERRED / REJECTED |
| Approver | User / project owner |
| Scope | Exact host, path, adapter, provider or environment |
| Permission granted | OS permission / credential / config opt-in / deployment |
| Data observed | Exact metadata/content class |
| Data retained | Exact fields and retention |
| Revocation/disable procedure | Documented steps |
| Validation evidence | Test, log, screenshot or CI run |
| Date/version | Decision timestamp and code/spec version |

**No approval is implied by the presence of a configuration option or by a successful local test.**
