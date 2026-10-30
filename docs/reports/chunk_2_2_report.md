# Chunk 2.2 — SQLite Persistence Foundation

**Status:** Implemented; CI verification pending.  
**Milestone alignment:** M0.3 / Phase A foundation.

## Delivered
- SQLModel tables for assets, AI tools, events, findings, finding-event links, secret-vault metadata, canary metadata, risk snapshots, policies and schema migrations.
- SQLite WAL mode, foreign-key enforcement and a 5-second busy timeout on every connection.
- Idempotent schema version 1 initialization and automatic parent-directory creation for file-backed databases.
- Persistence helpers for canonical events, findings and AI tools using caller-controlled transactions.
- Event metadata is serialized from the canonical Pydantic contract. Transient body references are excluded; sensitive HTTP headers are redacted by the contract boundary.
- Findings store masked evidence and link to existing events through foreign-key-constrained rows. Unknown event references are rejected before insertion.
- Timestamp, host, severity and status indexes support initial query paths. No raw-body/payload table exists.

## Tests
- Idempotent migration initialization and SQLite WAL/foreign-key pragmas.
- Event persistence and proof that transient body handles and test authorization values are absent.
- Finding persistence and event-link creation.
- Unknown event reference rejection, foreign-key enforcement and transaction rollback.
- Required schema tables and indexes.

## Scope boundary
This chunk establishes schema and persistence primitives only. It does not connect persistence to FastAPI, implement retention/forget workflows, add a migration CLI, or claim that raw data is securely zeroized in Python memory. Schema version 1 is the initial migration marker; future schema changes must be additive/versioned.

## Verification
Update with actual CI and security workflow results after the final implementation commit.
