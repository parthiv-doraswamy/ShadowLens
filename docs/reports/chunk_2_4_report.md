# Chunk 2.4 — Backend Application Lifecycle and Metadata Ingestion

**Status:** Implemented; CI and security workflow verification pending.  
**Base commit:** `5d0a63d754f8be1807f65f29b879a52a87b91062`

## Delivered

- Added an application factory and FastAPI lifespan that initializes SQLite schema/token state, starts the bounded event bus and collector supervisor, then shuts down collectors before draining the bus and disposing the database engine.
- Added first-run local bearer-token generation. The token is stored in `.shadowlens/access.token`; on POSIX the data directory is mode `0700` and the token file is mode `0600`. An explicit `SHADOWLENS_API_TOKEN` override is supported.
- Added `GET /api/health` as the sole unauthenticated route. It checks database connectivity and reports event-bus counters and configured collector status without exposing token material.
- Added authenticated `POST /api/events` for validated canonical metadata events. The transport-specific `IngestEvent` schema excludes collector-only `http.body_ref`, bounds HTTP header/provenance counts, and redacts sensitive headers before the event enters the queue.
- Protected Swagger UI and OpenAPI routes as well as operational API routes.
- Added lifecycle, persistence, token permission/reuse, bearer-auth, docs-auth, body-reference rejection and graceful-drain tests.
- Updated `.env.example`, `.gitignore`, backend/event-pipeline architecture and implementation backlog.

## Privacy and security boundaries

The HTTP endpoint does not accept raw request bodies or prompts and rejects a supplied `body_ref`. Sensitive request headers are redacted before queuing. No access token is returned by an API response or included in health output. The health route follows the explicit NFR-SEC-1 exception.

The ingestion response is `202 Accepted`: it confirms in-memory queue acceptance, not a completed database commit. The queue is volatile; a process crash before worker persistence can lose queued events. No real collector is enabled by default. Multipart HAR, JSONL, PCAP and proxy-log parsing are not implemented in this chunk.

## Verification

Tests added/updated:
- Database schema and health status on startup.
- Token creation, stable reuse and restrictive POSIX permissions.
- Bearer-token enforcement and protected docs/OpenAPI.
- Canonical event accepted and persisted with sensitive header redaction.
- Transport schema rejects `http.body_ref`.
- Collector shutdown precedes bus drain; accepted test event is persisted before engine disposal.

CI and security workflows were triggered by the implementation commit. Their actual run IDs and final conclusions are recorded after workflow completion; implementation is not marked verified until both workflows pass.
