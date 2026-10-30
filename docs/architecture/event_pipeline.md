# ShadowLens Event Pipeline Architecture

**Status:** Canonical processing design; bounded queue, SQLite event persistence and metadata-event API wiring are implemented. Real collectors and downstream analysis stages remain planned.  
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

The implemented M0 event bus uses a bounded `asyncio.Queue` (default capacity is a caller-selected setting; the primitive defaults to 256) and a fixed worker count. Producers may await `publish` to apply backpressure or use `publish_nowait` to receive an explicit `QueueFull`; an optional publish timeout is also explicit. The bus records accepted, successfully processed, processing-failed and rejected counts plus queue depth, active workers and intake state. Handler exceptions are isolated and counted; they do not terminate the worker. A failed handler invocation is not reported as successfully processed.

Shutdown first closes intake, waits for all accepted queue items to be acknowledged, then sends one sentinel per worker and awaits worker completion. This drains accepted events before worker exit. A caller that requires bounded shutdown time must enforce its own outer timeout and report an incomplete drain rather than silently discarding events.

Collectors implement a narrow async protocol receiving an event publisher and cooperative stop event. The supervisor runs each collector independently, records the latest exception/restart count, and restarts unexpected exits with capped exponential backoff. One failing collector does not stop its peers. Collectors should check the stop event and return promptly during shutdown.

The bus is connected to FastAPI and SQLite persistence through a canonical metadata-event intake route. The application configures queue capacity and worker count from environment settings. No production collector is enabled by default; the supervisor starts with an empty registry. The bus remains in-memory and is not crash-durable.

## 6. Payload lifecycle

Raw body data is held only in a bounded transient buffer for the minimum inspection window. It is not serialized into the canonical persisted event. Use a transient handle with clear ownership/release semantics; avoid unnecessary copies. Python memory zeroization is not guaranteed and must not be claimed. After inspection, only masked previews, HMAC fingerprints, typed redacted context and safe offsets/counts may be retained.

## 7. Evidence and finding linkage

A Finding links to one or more event IDs. Evidence records rule ID/version, source, tier, confidence, masked evidence, HMAC where applicable, offset and redacted context. Correlation findings link all contributing event/finding references in temporal order. Missing evidence is represented as unavailable, not fabricated.

## 8. Replay and simulation

Simulator input is synthetic and labelled. Replay traverses the same normalization/detection pipeline but must not execute shell commands, perform outbound exfiltration or plant canaries without explicit approval. Replay is read-only with respect to production records unless a user explicitly chooses a separate demo dataset.


## 9. FastAPI lifecycle and metadata intake

The application lifespan creates the SQLite engine, initializes the schema and first-run bearer token, starts the event bus, then starts the collector supervisor. Shutdown reverses the producer path: signal and await collectors first, close bus intake and drain accepted queue items second, and dispose the database engine last. Startup failure attempts cleanup before propagating the error.

`GET /api/health` is unauthenticated as the explicit NFR-SEC-1 exception. It checks the database with `SELECT 1` and reports bus counters plus collector state; it does not disclose the token or token-file path. `POST /api/events` requires a bearer token and accepts an `IngestEvent` transport schema. That schema inherits canonical event validation but deliberately omits `http.body_ref`, bounds HTTP header/provenance counts and redacts sensitive headers before enqueueing. No raw request body or prompt is accepted by this endpoint.

A `202` response confirms queue acceptance only. A worker persists the event metadata in its own transaction. Queue saturation returns a retryable `503`; database/handler failures increment the bus failure counter and cause health to report degraded status. The route does not implement multipart uploads: HAR, PCAP, JSONL and proxy-log parsers remain separate collector work.

The token is generated using a cryptographically secure random value at first startup and stored in an owner-only file under the local data directory. Operators may provide an explicit `SHADOWLENS_API_TOKEN` override. API documentation and the generated OpenAPI document are also protected so `/api/health` remains the only unauthenticated route.

The event bus is volatile. A process crash after queue acceptance but before a database commit can lose an event; the `202` response is not a durability guarantee.


## 10. Operational logs and failure reporting

Application lifecycle, HTTP request outcomes, database health-check failures, event-worker failures and collector restarts emit structured JSON records. HTTP logs contain only a server-generated request ID, method, route template, status and elapsed time. They intentionally omit query strings, headers, client addresses and request bodies. Sensitive field names and common bearer/API-key patterns are redacted at the structlog processor; values are size/depth bounded and arbitrary object representations are not logged.

Worker/collector failure diagnostics include the exception class and counters/backoff only, not exception messages. The collector supervisor retains only the exception class in its status. The default Uvicorn access logger is disabled to avoid logging raw request targets. This does not claim control over logs generated by third-party dependencies, the host operating system or external process supervisors.
