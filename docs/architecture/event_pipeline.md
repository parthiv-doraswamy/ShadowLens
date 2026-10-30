# ShadowLens Event Pipeline Architecture

**Status:** Canonical processing design; no event pipeline implemented yet.  
**Source:** Master Specification sections 0, 4–6, 8, 9 and 20 Phase A–D.

## 1. Pipeline contract

All collectors are replaceable adapters. They emit the same validated canonical Event contract. Collectors do not classify severity, create risk scores or make enforcement decisions.

## 2. Source adapters and visibility

| Adapter | Evidence source | Expected tier / limitations |
|---|---|---|
| Socket collector | psutil connection/process metadata | T1; attribution may be incomplete or permission-limited |
| PCAP parser | DNS, TCP, TLS ClientHello, plaintext HTTP | T1 metadata for encrypted TLS; T3 only for authorized plaintext captured in the file |
| HAR / JSONL / proxy logs | User-supplied structured request records | T3 only when source includes authorized plaintext; raw body remains transient |
| Loopback sniffer | Optional Scapy capture | T1/T3 according to actual visibility; permission-gated |
| Lens Gateway | Explicit client-to-loopback proxy request | T3 for client plaintext; optional, allowlisted, no MITM and no body persistence |
| Agent hooks | Structured tool-call/audit traces | T3 for supplied structured activity; missing fields remain unknown |
| Config scanner | Opt-in read-only AI-related metadata | Discovery evidence; no secret values or shell history |

## 3. Canonical Event envelope

The master spec defines event_id, timestamp, source, tier, hashed host_id, process metadata, network metadata, HTTP metadata with transient body_ref, AI provider/kind/model/sanctioned metadata and raw_visibility. Implement as Pydantic v2 models with:
- stable event ID and timezone-aware timestamp;
- enumerated source and visibility values;
- optional source-dependent fields;
- provenance and collection status;
- explicit distinction between observed fields, derived fields and unavailable fields;
- bounded metadata size and safe serialization;
- transient-only payload handle that is excluded from persistence/JSON output.

The exact JSON example in section 5.1 is the canonical starting contract. Any schema evolution must preserve its semantics and be versioned.

## 4. Processing stages

1. **Acquire:** adapter obtains source-specific observation.
2. **Validate:** parse and validate source data under size/time bounds.
3. **Normalize:** map into canonical Event, preserving original source and provenance.
4. **Classify:** match provider registry; keep unknown endpoint provisional.
5. **Inspect:** send transient plaintext to deterministic secret/PII/proprietary/canary inspectors only when authorized and actually available.
6. **Analyze:** process structured agent tool calls and T2 flow-shape windows as applicable.
7. **Correlate:** join evidence by event, host, process, tool, time window and destination; preserve ordered links.
8. **Score/map:** calculate deterministic risk and informational compliance controls.
9. **Persist:** write metadata and redacted evidence; never raw bodies.
10. **Publish:** expose API/SSE updates after successful transaction.
11. **Advise:** optional asynchronous LLM triage receives only the specified redacted DTO and cannot mutate deterministic state.

## 5. Queue and backpressure

Use a bounded asyncio.Queue and supervised workers. Queue capacity, worker concurrency, overflow policy and shutdown drain behavior are implementation decisions that must be documented and tested before M0 exit. No unbounded in-memory queue. No silent event loss: expose accepted/rejected/dropped counters and health state; prefer explicit backpressure or structured rejection over hidden drops. Isolate a failing collector and restart with backoff.

## 6. Payload lifecycle

Raw body data is held only in a bounded transient buffer for the minimum inspection window. It is not serialized into the canonical persisted event. Use a transient handle with clear ownership/release semantics; avoid unnecessary copies. Python memory zeroization is not guaranteed and must not be claimed. After inspection, only masked previews, HMAC fingerprints, typed redacted context and safe offsets/counts may be retained.

## 7. Evidence and finding linkage

A Finding links to one or more event IDs. Evidence records rule ID/version, source, tier, confidence, masked evidence, HMAC where applicable, offset and redacted context. Correlation findings link all contributing event/finding references in temporal order. Missing evidence is represented as unavailable, not fabricated.

## 8. Replay and simulation

Simulator input is synthetic and labelled. Replay traverses the same normalization/detection pipeline but must not execute shell commands, perform outbound exfiltration or plant canaries without explicit approval. Replay is read-only with respect to production records unless a user explicitly chooses a separate demo dataset.
