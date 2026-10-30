# Chunk 2.3 — Bounded Asynchronous Event Bus

**Status:** Implemented; CI/security verification pending.  
**Milestone alignment:** M0.4 / Phase A foundation.

## Delivered
- Bounded `asyncio.Queue` event bus with configurable capacity and worker count.
- Awaitable publication applies producer backpressure. Optional timeout rejects explicitly; nonblocking publication raises `QueueFull` on saturation. Intake-closed publication is rejected.
- Immutable stats snapshot exposes accepted, processed, processing-failed and rejected counts, queue depth, active workers and intake state.
- Worker handler exceptions are isolated and counted; workers continue processing subsequent events.
- Graceful stop closes intake, drains accepted queue items, sends worker sentinels and awaits worker completion.
- Collector protocol accepts a canonical Event publisher and cooperative stop event.
- Collector supervisor isolates collectors, records restart count/latest error and restarts unexpected failures with capped exponential backoff.
- Architecture documentation records queue semantics, shutdown behavior and integration boundaries.

## Tests
- Queue capacity and explicit saturation rejection.
- Awaitable backpressure and timeout accounting.
- Worker exception isolation and continuation.
- Queue drain and intake rejection after shutdown.
- Collector restart/backoff isolation and cooperative stop.
- Invalid configuration rejection.

## Scope boundary
The event bus is not yet wired to FastAPI, SQLite persistence, actual collectors or health endpoints. It does not claim durable queue semantics: events in the in-memory queue are lost if the process exits abruptly. A future application lifecycle layer must coordinate collector stop, queue drain and database writes. A caller needing bounded shutdown must impose a timeout and surface incomplete drain rather than silently discarding events.

## Verification
Update with actual CI and security workflow results after the final implementation commit.
