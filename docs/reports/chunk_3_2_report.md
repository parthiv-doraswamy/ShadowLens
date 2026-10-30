# Chunk 3.2 — HAR/JSONL and Proxy Log Ingestion

**Requirement:** REQ-COL-003 (P0)  
**Status:** Implemented on `feat/har-jsonl-ingestion-req-col-003`; CI/security verification pending.  
**Scope:** Safe import of HTTP request metadata from supported HAR, proxy JSON, JSONL and ShadowLens mock-log files.

## Delivered

- Added a metadata-only parser for HAR, mitmproxy JSON flow exports, nginx/squid-style JSONL and ShadowLens normalized mock-event JSON.
- Added format detection, UTF-8 validation, supported extension checks, 25 MiB file cap, 10,000-record cap and 1 MiB JSONL line cap.
- Malformed records are skipped with record number and a safe error code; source values and exception messages are not echoed.
- Converts imported records into canonical T1 `Event` contracts with `EventSource.LOG`, destination metadata, HTTP method/path, provider classification and field provenance.
- Sensitive HTTP headers are redacted by the existing canonical HTTP metadata contract before an event can be serialized or persisted.
- Request/response bodies are never copied into canonical events, error messages, logs or persistence.
- Added authenticated multipart `POST /api/ingest`; upload reads are bounded, upload handles are closed in a `finally` block, and events are queued through the existing bounded event bus.
- Added `shadowlens ingest <file>` to persist normalized metadata events locally.
- Added tests for the 500-entry/12-provider-call acceptance fixture, mitmproxy header encodings, nginx JSONL, ShadowLens mock format, malformed records, invalid/empty/oversized files, body/header non-retention, API auth and CLI persistence.

## Files changed

- `backend/app/ingestion/__init__.py`
- `backend/app/ingestion/logs.py`
- `backend/app/main.py`
- `backend/app/cli.py`
- `backend/pyproject.toml`
- `backend/tests/test_log_ingestion.py`
- `docs/requirements/acceptance_criteria.md`
- `docs/requirements/implementation_backlog.md`
- `docs/requirements/traceability_matrix.md`
- `README.md`

## Verification

- **Local test execution:** Not run through the remote GitHub editing session.
- **GitHub Actions:** CI and Security workflows triggered by this branch; results must be green before merge.
- No passing test result is claimed in this report.

## Explicit boundaries

- Imported events are T1 metadata. The importer does not decrypt TLS, infer request bodies, or upgrade visibility to T3.
- The master specification says request bodies should be routed to an inspector while not being persisted. The current repository does not yet contain the detector/inspector handoff. This chunk discards body content safely; transient body inspection remains pending the detection/inspection phase and is not claimed as implemented.
- Supported JSON variants are the documented HAR, mitmproxy flow list, structured JSONL and ShadowLens normalized event format. Arbitrary vendor-specific proxy schemas are not claimed.
- The initial log-import cap is 25 MiB and 10,000 records; these are implementation safety limits, not master-spec performance guarantees.

## Traceability

`REQ-COL-003` maps to `backend/app/ingestion/logs.py`, authenticated `POST /api/ingest`, `shadowlens ingest` and `backend/tests/test_log_ingestion.py`. Body-to-inspector routing remains an open acceptance item.
