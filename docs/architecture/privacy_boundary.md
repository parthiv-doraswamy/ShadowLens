# ShadowLens Privacy Boundary

**Status:** Mandatory architecture constraint; not a privacy certification.  
**Source:** Master Specification sections 0, 1, 3, 9, 10 and 22.

## 1. Data boundary

ShadowLens is local-first and loopback-bound by default. Collection is limited to configured, supported sources. The product must show what it can and cannot observe. No telemetry or external requests occur unless the optional triage feature is explicitly enabled.

## 2. Data classes and handling

| Data | Permitted processing | Persistence / disclosure |
|---|---|---|
| Socket/process metadata | Collect supported metadata and provenance | Persist minimized metadata; disclose OS visibility limits |
| Encrypted TLS traffic | Observe permitted metadata such as endpoint/SNI/ALPN/flow shape | Never claim body inspection; no TLS decryption |
| Authorized plaintext body | Inspect transiently for deterministic rules | Never persist raw body; retain masked/HMAC/redacted evidence only |
| Secret candidate | Validate and contextualize | HMAC-SHA256 with install salt + masked first 4/last 2 preview |
| PII | Validate and redact all sensitive spans | Typed placeholders in ±40-character context |
| Agent trace | Parse supplied structured events | Persist normalized action/evidence with source provenance |
| Config metadata | Opt-in, read-only, allowlisted AI-related metadata | Never read .env values, shell history or credential stores |
| Hostname/username | Use for local correlation where required | Hash in exports unless include-identifiers is explicit |
| LLM triage context | Send minimum redacted DTO only when enabled | Never send raw secrets or full prompts |
| Simulator data | Synthetic labelled test events | Keep clearly labelled as demo data |

## 3. Raw payload lifecycle

1. Receive authorized plaintext from an explicitly supported source.
2. Place it in a bounded transient buffer with a strict size and lifetime.
3. Inspect synchronously or through a controlled worker without writing body to disk.
4. Create masked preview, HMAC fingerprint, safe offsets/counts and redacted context.
5. Persist only safe evidence and metadata.
6. Release references and avoid unnecessary copies.

Do not claim guaranteed memory zeroization in Python.

## 4. External network boundary

- Default: no telemetry and no external request.
- Optional remote triage: explicit user enablement and credentials; only redacted context.
- Local Ollama: optional local endpoint.
- Lens Gateway: explicit opt-in, loopback-only, upstream-restricted, SSRF-resistant, audit-only and no body persistence. It is not a TLS MITM.
- No public deployment without a separate user approval and synthetic demo data.

## 5. Configuration discovery boundary

Config scanning is opt-in, read-only and metadata-minimized. Restrict it to allowlisted AI-related paths/keys and supported manifests. Do not inspect shell history, .env values, credential stores or secret contents. Environment variable names may be discovered; values are not read as secret contents (source specifies values hashed where relevant). A process/package name is a clue, not proof of active AI use.

## 6. Visibility honesty

- T1: observed metadata.
- T2: inferred flow-shape pattern; confidence at most the source-specified 0.7.
- T3: verified content from authorized plaintext or structured trace.
- DERIVED: deterministic calculation, such as risk.
- UNAVAILABLE: missing due to encryption, permission, unsupported source or absent telemetry.

LLM confidence cannot promote T1/T2 to T3. psutil is not universal file-read/shell-command auditing.

## 7. User controls

Explicit gates are required for config scanning, canary placement, live loopback capture, gateway enablement, remote/local LLM triage and deployment. Do not auto-elevate privileges. The forget operation irreversibly wipes DB, vault and salt; its UX must not report success before verified completion.

## 8. Privacy validation

Acceptance tests must prove that known raw secrets do not appear in DB, logs, traces, exports or default API responses; redaction is idempotent; HMAC storage is stable under the install salt; exports hash identifiers by default; and core behavior works with triage disabled.
