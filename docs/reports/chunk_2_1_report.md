# Chunk 2.1 — Canonical Domain Contracts

**Status:** Implemented; verification pending.  
**Milestone alignment:** M0.2 / Phase A foundation.

## Delivered
- Versioned Pydantic v2 contracts for canonical Event, Finding, AI tool, evidence, process/network/HTTP/AI metadata, provenance and collection coverage.
- Strict enum vocabularies for event sources, visibility tiers, raw visibility, finding categories/severity/status, collection state and tool kind.
- UUIDv4 identifiers, timezone-aware timestamps, bounded fields, numeric/range checks and forbidden unknown fields.
- Sensitive HTTP header values are redacted at the contract boundary.
- The transient `body_ref` may exist in memory but is excluded from model serialization and repr.
- Visibility mapping is enforced: T1/metadata, T2/shape, T3/content. DERIVED and UNAVAILABLE remain separate provenance states.

## Tests
- Canonical valid event and finding fixtures.
- Invalid/naive timestamps, invalid visibility combinations, unknown fields, invalid ports and out-of-range confidence.
- Serialization exclusion for transient body references and secret-bearing headers.
- Provenance state requirements and tool/coverage contracts.

## Scope boundary
No database, migrations, queue, collector, detection engine, authentication or API integration is included. Those are later foundation chunks. These contracts do not claim that the source data was collected or independently verified.

## Verification
Update this report with actual CI/security results after the workflow run for the final implementation commit.
