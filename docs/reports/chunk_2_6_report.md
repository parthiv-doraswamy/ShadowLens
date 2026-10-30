# Chunk 2.6 — Local Runtime Settings and CLI

**Status:** Implemented; CI/security verification pending.
**Base commit:** bfb3396a4dbf15a35e422e235be217b9b72817d1

## Delivered

- Added app.config using Pydantic Settings for environment and optional .env loading, local data/token/database paths, host/port, CORS, queue capacity, workers, ingest timeout and log level.
- Host validation accepts only localhost or a literal loopback IP. CORS entries must be local HTTP(S) origins; wildcard and remote origins, credentials, paths and user information are rejected.
- Integrated settings into FastAPI app creation and configured CORSMiddleware with no credentials, a narrow method/header allowlist and X-Request-ID exposure.
- Added the shadowlens console script with init and serve commands.
- shadowlens init creates the local data directory, first-run bearer token, SQLite schema and a comments-only, non-enforcing policy starter. Existing policy files are preserved.
- shadowlens serve starts the API via Uvicorn on loopback only and disables Uvicorn access logging. --reload is available for development.
- serve --live and serve --gateway fail closed with an explicit unavailable error; no packet capture or proxy is started.
- SQLite initialization creates new parent directories with restrictive permissions, uses a restrictive POSIX umask when creating files, and sets the database file to owner read/write. Existing parent directory permissions are preserved.
- Updated root/backend quick-starts, .env.example, architecture and backlog documentation.

## Privacy and safety

The CLI never prints the generated token; it reports the token file location. The token file is owner-only on POSIX. The starter policy contains comments only; no active rules are invented or executed. Host and CORS validation prevent accidental LAN binding/origins through the supported CLI/configuration path.

The loopback guarantee applies to shadowlens serve. A user who bypasses the CLI and directly launches Uvicorn can override its bind address; direct custom server invocation is not the supported launch path. Windows filesystem permission behavior is not claimed equivalent to POSIX modes.

## Tests added

- Default settings and local CORS values.
- Reject non-loopback host addresses and remote/malformed CORS origins.
- IPv6 loopback and blank API-token behavior.
- Reject unsupported database URLs and weak operator tokens.
- init creates token/database/policy starter with expected POSIX permissions and is idempotent.
- init preserves existing parent directory permissions and operator-owned policy content.
- serve uses loopback, configured port and disables Uvicorn access logs.
- Unimplemented live/gateway switches and remote host overrides fail closed.
- FastAPI CORS preflight allows configured local origin and omits the allow-origin header for a remote origin.

CI and Security are triggered on the implementation commit. Final workflow conclusions will be recorded after they complete.
