"""Bounded asynchronous event bus and supervised collector lifecycle."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from app.models.contracts import Event

EventHandler = Callable[[Event], Awaitable[None]]
EventPublisher = Callable[[Event], Awaitable[None]]


class Collector(Protocol):
    """A collector repeatedly observes its source until the stop event is set."""

    async def run(self, publish: EventPublisher, stop_event: asyncio.Event) -> None:
        """Collect and publish validated canonical events."""


@dataclass(frozen=True, slots=True)
class BusStats:
    accepted: int
    processed: int
    processing_failed: int
    rejected: int
    queued: int
    workers: int
    accepting: bool


class EventBus:
    """Bounded asyncio queue with explicit backpressure and worker accounting."""

    def __init__(self, handler: EventHandler, capacity: int = 256, workers: int = 1) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        if workers < 1:
            raise ValueError("workers must be at least 1")
        self._handler = handler
        self._queue: asyncio.Queue[Event | None] = asyncio.Queue(maxsize=capacity)
        self._worker_count = workers
        self._tasks: list[asyncio.Task[None]] = []
        self._accepted = 0
        self._processed = 0
        self._processing_failed = 0
        self._rejected = 0
        self._accepting = False
        self._started = False

    async def start(self) -> None:
        """Start the configured workers exactly once."""
        if self._started:
            return
        self._accepting = True
        self._started = True
        self._tasks = [
            asyncio.create_task(self._worker(index), name=f"shadowlens-event-worker-{index}")
            for index in range(self._worker_count)
        ]

    async def publish(self, event: Event, timeout: float | None = None) -> None:
        """Enqueue an event; block under pressure or reject on an explicit timeout."""
        if not self._accepting:
            self._rejected += 1
            raise RuntimeError("event bus is not accepting events")
        try:
            if timeout is None:
                await self._queue.put(event)
            else:
                if timeout <= 0:
                    raise ValueError("timeout must be positive")
                await asyncio.wait_for(self._queue.put(event), timeout=timeout)
        except TimeoutError:
            self._rejected += 1
            raise
        self._accepted += 1

    def publish_nowait(self, event: Event) -> None:
        """Enqueue without waiting; queue saturation is visible to the caller."""
        if not self._accepting:
            self._rejected += 1
            raise RuntimeError("event bus is not accepting events")
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self._rejected += 1
            raise
        self._accepted += 1

    async def _worker(self, _index: int) -> None:
        while True:
            item = await self._queue.get()
            try:
                if item is None:
                    return
                try:
                    await self._handler(item)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    self._processing_failed += 1
                else:
                    self._processed += 1
            finally:
                self._queue.task_done()

    async def stop(self) -> None:
        """Stop intake, drain accepted events, then stop all workers."""
        if not self._started:
            return
        self._accepting = False
        await self._queue.join()
        for _ in self._tasks:
            await self._queue.put(None)
        await asyncio.gather(*self._tasks)
        self._tasks.clear()
        self._started = False

    def stats(self) -> BusStats:
        return BusStats(
            accepted=self._accepted,
            processed=self._processed,
            processing_failed=self._processing_failed,
            rejected=self._rejected,
            queued=self._queue.qsize(),
            workers=sum(not task.done() for task in self._tasks),
            accepting=self._accepting,
        )


@dataclass(frozen=True, slots=True)
class CollectorStatus:
    name: str
    running: bool
    restarts: int
    last_error: str | None


class CollectorSupervisor:
    """Run collectors independently and restart failures with capped backoff."""

    def __init__(
        self,
        collectors: dict[str, Collector],
        publish: EventPublisher,
        *,
        initial_backoff: float = 0.25,
        max_backoff: float = 10.0,
    ) -> None:
        if initial_backoff <= 0 or max_backoff < initial_backoff:
            raise ValueError("backoff bounds must be positive and max >= initial")
        self._collectors = collectors
        self._publish = publish
        self._initial_backoff = initial_backoff
        self._max_backoff = max_backoff
        self._stop_event = asyncio.Event()
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._restarts = dict.fromkeys(collectors, 0)
        self._last_errors: dict[str, str | None] = dict.fromkeys(collectors, None)

    async def start(self) -> None:
        """Start one independent supervisor task per configured collector."""
        if self._tasks:
            return
        self._stop_event.clear()
        self._tasks = {
            name: asyncio.create_task(self._run_one(name, collector), name=f"collector-{name}")
            for name, collector in self._collectors.items()
        }

    async def _run_one(self, name: str, collector: Collector) -> None:
        delay = self._initial_backoff
        while not self._stop_event.is_set():
            try:
                await collector.run(self._publish, self._stop_event)
                if self._stop_event.is_set():
                    return
                raise RuntimeError("collector exited unexpectedly")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._last_errors[name] = f"{type(exc).__name__}: {exc}"
                self._restarts[name] += 1
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
                except TimeoutError:
                    pass
                delay = min(delay * 2, self._max_backoff)

    async def stop(self) -> None:
        """Signal all collectors and wait for their cooperative shutdown."""
        self._stop_event.set()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    def statuses(self) -> tuple[CollectorStatus, ...]:
        return tuple(
            CollectorStatus(
                name=name,
                running=name in self._tasks and not self._tasks[name].done(),
                restarts=self._restarts[name],
                last_error=self._last_errors[name],
            )
            for name in self._collectors
        )
