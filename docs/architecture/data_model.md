# ShadowLens Data Model and Contract Architecture

**Status:** Logical model derived from the master specification; schema migrations not implemented.  
**Source:** Master Specification sections 5, 7, 8, 9 and 11.

## 1. Canonical entities

| Entity | Identity | Key attributes | Persistence rule |
|---|---|---|---|
| Asset | host_id | hostname_hash, OS, first_seen, last_seen | Hash machine/host identifiers where specified |
| AITool | tool_id | host_id, name, kind, provider, sanctioned, discovery, seen times, capabilities | Store observed/inferred provenance |
| Event | event_id | timestamp, host/tool, source, tier, provider, destination, process, metadata | No raw request body |
| Finding | finding_id | event links, category, rule_id/version, severity, confidence, tier, evidence, controls, status, triage | Evidence masked/redacted |
| FindingEvent | finding_id + event_id | link relationship | Supports multi-event correlation |
| SecretVaultEntry | HMAC | kind, first_seen, seen_count, masked preview | HMAC-SHA256(install_salt, value); never raw secret |
| Canary | canary_id | kind, HMAC, planted_path, created, triggered_at | Synthetic/user-planted only |
| RiskSnapshot | timestamp + scope + scope_id | score, breakdown | Deterministic and versioned |
| Policy | policy_id/version | YAML, active | Pydantic-validated; candidate simulation isolated |

## 2. Canonical Event fields

Use the source section 5.1 example as the starting point:
- event_id, ts, source, tier, host_id;
- process: pid, name, exe, user, cmdline_hash;
- net: dst_host, dst_ip, dst_port, proto, sni, ja4, bytes_out/in, direction, duration_ms;
- http: method, path, redacted headers, transient body_ref, stream;
- ai: provider, kind, model, sanctioned;
- raw_visibility.

Fields are optional where source does not expose them. Do not fill unknown values with guesses. Keep a source/provenance marker for every important field. A transient body_ref is an in-process handle only and must never be persisted.

## 3. Canonical Finding fields

Use the source section 5.2 example:
- finding_id and linked event_ids;
- category and rule_id;
- severity and confidence;
- tier;
- evidence: masked preview, HMAC, offset, context_redacted;
- mapped_controls;
- status;
- optional triage object.

Extend only with explicit implementation needs such as detector version, timestamps and provenance; document the extension and preserve source semantics.

## 4. Visibility and evidence types

T1 = observed metadata. T2 = inferred flow shape. T3 = verified content from an authorized plaintext/structured source. DERIVED = deterministic computed field such as risk score. UNAVAILABLE = source data not observable due to encryption, permissions, unsupported source or missing telemetry. Do not conflate these dimensions.

## 5. Persistence model

The master schema identifies:
- assets
- ai_tools
- events
- findings
- finding_events
- secret_vault
- canaries
- risk_snapshots
- policies

Use SQLite WAL and SQLModel. Preserve indexes on event timestamp and finding severity/status from the source DDL. Add foreign keys, migrations, retention and transaction rules during implementation. Never add a raw payload/body table.

## 6. API DTO boundaries

Separate persisted/domain models from request and response DTOs. API outputs must be redacted by default. Upload request models enforce file type/size limits. LLM triage DTO contains only rule_id, category, masked evidence, context_redacted, provider, tool, tier and autonomy_level.

## 7. Data lifecycle

Raw payload → bounded transient buffer → deterministic inspection → masked/HMAC/redacted evidence → SQLite. The raw buffer reference is released after inspection. Exports hash hostnames/usernames unless include-identifiers is explicitly requested. Forget operation removes database, vault and install salt.

## 8. Schema evolution

Version canonical event and finding contracts. Use migrations for SQLite changes. A change to field meaning, visibility semantics, retention or redaction requires spec-first review and updated acceptance/traceability tests.
