"""FastAPI application factory and privacy-safe event ingestion lifecycle."""
from __future__ import annotations

import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.api_schemas import IngestEvent
from app.bus.event_bus import Collector, CollectorSupervisor, EventBus
from app.models.contracts import Event
from app.persistence import (
    create_database_engine,
    initialize_database,
    save_event,
    session_scope,
)
from app.security import load_or_create_api_token


def _int_setting(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < 1:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _float_setting(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


async def _persist_event(engine: Engine, event: Event) -> None:
    """Persist one canonical event in its own transaction."""
    with session_scope(engine) as session:
        save_event(session, event)


def create_app(
    *,
    database_url: str | None = None,
    token_path: Path | None = None,
    collectors: dict[str, Collector] | None = None,
    queue_capacity: int | None = None,
    event_workers: int | None = None,
    publish_timeout_seconds: float | None = None,
) -> FastAPI:
    """Create an isolated application, suitable for local service and tests."""
    capacity = (
        queue_capacity
        if queue_capacity is not None
        else _int_setting("SHADOWLENS_EVENT_QUEUE_CAPACITY", 256)
    )
    workers = (
        event_workers
        if event_workers is not None
        else _int_setting("SHADOWLENS_EVENT_WORKERS", 1)
    )
    publish_timeout = (
        publish_timeout_seconds
        if publish_timeout_seconds is not None
        else _float_setting("SHADOWLENS_INGEST_TIMEOUT_SECONDS", 1.0)
    )
    if capacity < 1 or workers < 1 or publish_timeout <= 0:
        raise ValueError("queue capacity, workers and publish timeout must be positive")

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(database_url)
        bus = EventBus(
            handler=lambda event: _persist_event(engine, event),
            capacity=capacity,
            workers=workers,
        )
        supervisor = CollectorSupervisor(collectors or {}, publish=bus.publish)
        try:
            initialize_database(engine)
            api_token = load_or_create_api_token(token_path)
            await bus.start()
            await supervisor.start()
        except BaseException:
            try:
                await supervisor.stop()
            finally:
                try:
                    await bus.stop()
                finally:
                    engine.dispose()
            raise

        application.state.database_engine = engine
        application.state.event_bus = bus
        application.state.collector_supervisor = supervisor
        application.state.api_token = api_token

        try:
            yield
        finally:
            # Producers stop before intake closes; the bus then drains accepted work.
            try:
                await supervisor.stop()
            finally:
                try:
                    await bus.stop()
                finally:
                    engine.dispose()

    application = FastAPI(
        title="ShadowLens API",
        version="0.2.0",
        docs_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    bearer_scheme = HTTPBearer(auto_error=False)

    async def require_api_token(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> None:
        expected_token: str = request.app.state.api_token
        if credentials is None or not secrets.compare_digest(
            credentials.credentials, expected_token
        ):
            raise HTTPException(
                status_code=401,
                detail="A valid bearer token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @application.get("/api/health", tags=["system"])
    async def health(request: Request) -> JSONResponse:
        """Report database, queue and adapter status without exposing secrets."""
        engine: Engine = request.app.state.database_engine
        event_bus: EventBus = request.app.state.event_bus
        supervisor: CollectorSupervisor = request.app.state.collector_supervisor

        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            database_status = "ok"
        except SQLAlchemyError:
            database_status = "unavailable"

        bus_stats = event_bus.stats()
        bus_status = "accepting" if bus_stats.accepting else "unavailable"
        collector_statuses = supervisor.statuses()
        collector_items = [
            {
                "name": status.name,
                "running": status.running,
                "restarts": status.restarts,
                "last_error": status.last_error,
            }
            for status in collector_statuses
        ]
        if not collector_statuses:
            collector_state = "not_configured"
        elif all(
            status.running and status.last_error is None
            for status in collector_statuses
        ):
            collector_state = "running"
        else:
            collector_state = "degraded"

        healthy = (
            database_status == "ok"
            and bus_status == "accepting"
            and bus_stats.processing_failed == 0
            and collector_state != "degraded"
        )
        payload = {
            "status": "ok" if healthy else "degraded",
            "database": {"status": database_status},
            "event_bus": {
                "status": bus_status,
                "accepted": bus_stats.accepted,
                "processed": bus_stats.processed,
                "processing_failed": bus_stats.processing_failed,
                "rejected": bus_stats.rejected,
                "queued": bus_stats.queued,
                "workers": bus_stats.workers,
            },
            "collectors": {"status": collector_state, "items": collector_items},
        }
        return JSONResponse(status_code=200 if healthy else 503, content=payload)

    @application.post(
        "/api/events",
        status_code=202,
        tags=["events"],
        dependencies=[Depends(require_api_token)],
    )
    async def ingest_event(
        payload: IngestEvent,
        request: Request,
    ) -> dict[str, str]:
        """Queue one validated metadata event; raw bodies are not an API input."""
        event = payload.to_event()
        event_bus: EventBus = request.app.state.event_bus
        try:
            await event_bus.publish(event, timeout=publish_timeout)
        except TimeoutError as exc:
            raise HTTPException(
                status_code=503,
                detail="event intake queue is full; retry later",
                headers={"Retry-After": "1"},
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail="event intake is unavailable",
                headers={"Retry-After": "1"},
            ) from exc
        return {"status": "accepted", "event_id": str(event.event_id)}

    @application.get(
        "/api/openapi.json",
        include_in_schema=False,
        dependencies=[Depends(require_api_token)],
    )
    async def openapi_schema() -> dict[str, object]:
        """Expose the generated schema only to authenticated local operators."""
        return application.openapi()

    @application.get(
        "/api/docs",
        include_in_schema=False,
        dependencies=[Depends(require_api_token)],
    )
    async def swagger_docs() -> HTMLResponse:
        """Serve Swagger UI behind the same bearer-token boundary as the API."""
        return get_swagger_ui_html(
            openapi_url="/api/openapi.json",
            title="ShadowLens API",
        )

    return application


app = create_app()
