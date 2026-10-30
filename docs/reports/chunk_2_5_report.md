# Chunk 2.5 — Structured Logging, Redaction and Operational Hardening

**Status:** Implemented; CI/security verification pending.  
**Base commit:** `0a198db4b49a185c2a135df2fed54c9f290dcb98`

## Delivered

- Added `app/observability.py` with structlog JSON output, ISO UTC timestamps, log levels, conservative recursive redaction, bounded strings/collections/depth and safe handling of non-JSON objects.
- Added an environment log-level setting: `SHADOWLENS_LOG_LEVEL`.
- Added privacy-safe HTTP access logs containing method, route template, status, duration and a server-generated request ID only.
- Added `X-Request-ID` to handled HTTP responses and generic internal-error responses.
- Disabled Uvicorn's default access logger because it can print the raw request target and query string.
- Added application start/stop, database health failure, event processing failure and collector restart diagnostics.
- Failure logs and collector status record exception class, not raw exception message.
- Added tests for credential redaction, sensitive nested keys, bounded log values, JSON access logs, query/header exclusion, worker error logs and generic 500 responses.

## Privacy boundary

The application access logger never reads request headers or bodies for logging and does not record query strings or client addresses. Sensitive field names such as authorization, cookie, password, secret, token, prompt, body, payload, content and raw are redacted recursively. Common bearer/API-key patterns and secret assignments are scrubbed from remaining strings.

The application disables Uvicorn access lines, but this does not sanitize third-party libraries, host OS logs or external process-supervisor logs. The configured JSON logging is for application-owned records, not a system-wide log collection agent.

## Verification

New tests:
- Sensitive keys and credential patterns redacted in nested records.
- String, collection and nesting bounds enforced.
- HTTP access logs omit query-string secrets and Authorization headers.
- Worker failure logs emit exception type, not exception message.
- Unhandled application exceptions return a generic 500 payload with a request ID.

CI and Security are triggered on the implementation commit. Their actual run IDs and conclusions will be recorded after they complete.
