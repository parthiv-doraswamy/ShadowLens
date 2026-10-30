import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.bus.event_bus import CollectorSupervisor, EventBus
from app.models.contracts import Event


def make_event() -> Event:
    return Event.model_validate({
        "event_id": str(uuid4()),
        "ts": datetime.now(UTC).isoformat(),
        "source": "socket",
        "tier": "T1",
        "host_id": "host-hash",
        "raw_visibility": "metadata",
    })


@pytest.mark.asyncio
async def test_bounded_queue_rejects_without_silent_drop() -> None:
    gate = asyncio.Event()
    started = asyncio.Event()

    async def handler(_event: Event) -> None:
        started.set()
        await gate.wait()

    bus = EventBus(handler, capacity=1, workers=1)
    await bus.start()
    bus.publish_nowait(make_event())
    await started.wait()
    bus.publish_nowait(make_event())
    with pytest.raises(asyncio.QueueFull):
        bus.publish_nowait(make_event())
    stats = bus.stats()
    assert stats.accepted == 2
    assert stats.rejected == 1
    assert stats.queued == 1
    gate.set()
    await bus.stop()
    assert bus.stats().processed == 2


@pytest.mark.asyncio
async def test_async_publish_applies_backpressure_and_timeout_is_counted() -> None:
    gate = asyncio.Event()
    entered = asyncio.Event()

    async def handler(_event: Event) -> None:
        entered.set()
        await gate.wait()

    bus = EventBus(handler, capacity=1)
    await bus.start()
    await bus.publish(make_event())
    await entered.wait()
    await bus.publish(make_event())
    with pytest.raises(TimeoutError):
        await bus.publish(make_event(), timeout=0.01)
    assert bus.stats().rejected == 1
    gate.set()
    await bus.stop()


@pytest.mark.asyncio
async def test_worker_failure_is_counted_and_worker_continues() -> None:
    calls = 0

    async def handler(_event: Event) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("synthetic handler failure")

    bus = EventBus(handler, capacity=2)
    await bus.start()
    await bus.publish(make_event())
    await bus.publish(make_event())
    await bus.stop()
    stats = bus.stats()
    assert stats.accepted == 2
    assert stats.processing_failed == 1
    assert stats.processed == 1


@pytest.mark.asyncio
async def test_stop_drains_queue_and_rejects_new_events() -> None:
    processed: list[str] = []

    async def handler(event: Event) -> None:
        processed.append(str(event.event_id))

    bus = EventBus(handler, capacity=3, workers=2)
    await bus.start()
    events = [make_event() for _ in range(3)]
    for event in events:
        await bus.publish(event)
    await bus.stop()
    assert set(processed) == {str(event.event_id) for event in events}
    assert bus.stats().queued == 0
    with pytest.raises(RuntimeError, match="not accepting"):
        await bus.publish(make_event())


@pytest.mark.asyncio
async def test_collector_supervisor_restarts_one_failed_collector() -> None:
    class FlakyCollector:
        def __init__(self) -> None:
            self.calls = 0

        async def run(self, _publish, stop_event: asyncio.Event) -> None:
            self.calls += 1
            if self.calls == 1:
                raise OSError("temporary source failure")
            await stop_event.wait()

    class StableCollector:
        async def run(self, _publish, stop_event: asyncio.Event) -> None:
            await stop_event.wait()

    flaky = FlakyCollector()
    supervisor = CollectorSupervisor(
        {"flaky": flaky, "stable": StableCollector()},
        publish=lambda _event: asyncio.sleep(0),
        initial_backoff=0.001,
        max_backoff=0.002,
    )
    await supervisor.start()
    for _ in range(100):
        if flaky.calls >= 2:
            break
        await asyncio.sleep(0.002)
    statuses = {status.name: status for status in supervisor.statuses()}
    assert flaky.calls >= 2
    assert statuses["flaky"].restarts >= 1
    assert statuses["flaky"].last_error == "OSError: temporary source failure"
    assert statuses["stable"].running
    await supervisor.stop()
    assert all(not status.running for status in supervisor.statuses())


@pytest.mark.asyncio
async def test_invalid_queue_and_backoff_configuration_rejected() -> None:
    async def handler(_event: Event) -> None:
        return None

    with pytest.raises(ValueError):
        EventBus(handler, capacity=0)
    with pytest.raises(ValueError):
        CollectorSupervisor({}, publish=lambda _event: asyncio.sleep(0),
                            initial_backoff=2, max_backoff=1)
