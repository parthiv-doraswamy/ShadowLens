"""FastAPI application factory and privacy-safe event ingestion lifecycle."""
from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.api_schemas import IngestEvent
from app.bus.event_bus import Collector, CollectorSupervisor, EventBus
from app.config import Settings
from app.ingestion.logs import MAX_IMPORT_BYTES, ImportValidationError, parse_log_bytes
from app.models.contracts import Event
from app.observability import configure_structured_logging, get_logger
from app.persistence import (
    create_database_engine,
    initialize_database,
    save_event,
    session_scope,
)
from app.security import load_or_create_api_token


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
    settings: Settings | None = None,
) -> FastAPI:
    """Create an isolated application, suitable for local service and tests."""
    runtime_settings = settings or Settings()
    capacity = (
        queue_capacity
        if queue_capacity is not None
        else runtime_settings.event_queue_capacity
    )
    workers = (
        event_workers
        if event_workers is not None
        else runtime_settings.event_workers
    )
    publish_timeout = (
        publish_timeout_seconds
        if publish_timeout_seconds is not None
        else runtime_settings.ingest_timeout_seconds
    )
    if capacity < 1 or workers < 1 or publish_timeout <= 0:
        raise ValueError("queue capacity, workers and publish timeout must be positive")

    effective_database_url = (
        database_url
        if database_url is not None
        else runtime_settings.resolved_database_url
    )
    effective_token_path = token_path or runtime_settings.resolved_token_file
    configured_token = (
        runtime_settings.api_token.get_secret_value()
        if runtime_settings.api_token is not None
        else None
    )
    log_level = runtime_settings.log_level
    configure_structured_logging(log_level)
    logger = get_logger("shadowlens.application")

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(effective_database_url)
        bus = EventBus(
            handler=lambda event: _persist_event(engine, event),
            capacity=capacity,
            workers=workers,
        )
        supervisor = CollectorSupervisor(collectors or {}, publish=bus.publish)
        try:
            initialize_database(engine)
            api_token = load_or_create_api_token(
                effective_token_path,
                configured_token=configured_token,
            )
            await bus.start()
            await supervisor.start()
            logger.info(
                "application_started",
                queue_capacity=capacity,
                event_workers=workers,
                collector_count=len(collectors or {}),
            )
        except BaseException as exc:
            logger.error("application_start_failed", exception_type=type(exc).__name__)
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
            logger.info("application_stopping")
            try:
                await supervisor.stop()
            finally:
                try:
                    await bus.stop()
                    stats = bus.stats()
                    logger.info(
                        "event_bus_stopped",
                        accepted=stats.accepted,
                        processed=stats.processed,
                        processing_failed=stats.processing_failed,
                        rejected=stats.rejected,
                        queued=stats.queued,
                    )
                finally:
                    engine.dispose()

    application = FastAPI(
        title="ShadowLens API",
        version="0.2.0",
        docs_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_allow_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

    @application.middleware("http")
    async def privacy_safe_access_log(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Log route templates and outcomes only; never inspect request headers or bodies."""
        request_id = uuid4().hex
        request.state.request_id = request_id
        clear_contextvars()
        bind_contextvars(request_id=request_id)
        started = perf_counter()
        status_code = 500
        response_received = False
        try:
            response = await call_next(request)
            status_code = response.status_code
            response_received = True
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            logger.error(
                "http_request_failed",
                method=request.method,
                route="unhandled",
                status_code=status_code,
                exception_type=type(exc).__name__,
                duration_ms=round((perf_counter() - started) * 1000, 2),
            )
            raise
        finally:
            route = request.scope.get("route")
            route_path = getattr(route, "path", None)
            route_template = route_path if isinstance(route_path, str) else "unmatched"
            if response_received:
                logger.info(
                    "http_request_completed",
                    method=request.method,
                    route=route_template,
                    status_code=status_code,
                    duration_ms=round((perf_counter() - started) * 1000, 2),
                )
            clear_contextvars()

    @application.exception_handler(RequestValidationError)
    async def sanitized_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return schema errors without echoing untrusted request values."""
        safe_errors: list[dict[str, object]] = []
        for error in exc.errors():
            safe_errors.append({
                "loc": list(error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(status_code=422, content={"detail": safe_errors})

    @application.exception_handler(Exception)
    async def sanitized_internal_error(_request: Request, _exc: Exception) -> JSONResponse:
        """Avoid returning framework exception messages to API clients."""
        request_id = getattr(_request.state, "request_id", None)
        headers = {"X-Request-ID": request_id} if isinstance(request_id, str) else None
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=headers,
        )

    bearer_dependency = Depends(HTTPBearer(auto_error=False))

    async def require_api_token(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = bearer_dependency,
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
        except SQLAlchemyError as exc:
            database_status = "unavailable"
            logger.warning(
                "database_health_check_failed",
                exception_type=type(exc).__name__,
            )

        bus_stats = event_bus.stats()
        bus_status = "accepting" if bus_stats.accepting else "unavailable"
        collector_statuses = supervisor.statuses()
        collector_items = [
            {
                "name": status.name,
                "running": status.running,
                "restarts": status.restarts,
                # Exception messages can contain paths or source data; health is public.
                "last_error_present": status.last_error is not None,
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
        "/api/ingest",
        status_code=202,
        tags=["ingestion"],
        dependencies=[Depends(require_api_token)],
    )
    async def ingest_log_file(
        request: Request,
        file: UploadFile = File(...),  # noqa: B008
    ) -> dict[str, object]:
        """Import HAR/JSON/JSONL metadata; request and response bodies are discarded."""
        filename = file.filename or ""
        data = bytearray()
        try:
            while chunk := await file.read(64 * 1024):
                if len(data) + len(chunk) > MAX_IMPORT_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="import exceeds the 25 MiB size limit",
                    )
                data.extend(chunk)
            report = parse_log_bytes(filename, bytes(data))
        except ImportValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        finally:
            await file.close()

        event_bus: EventBus = request.app.state.event_bus
        accepted = 0
        for event in report.events:
            try:
                await event_bus.publish(event, timeout=publish_timeout)
            except TimeoutError:
                break
            except RuntimeError:
                break
            accepted += 1
        return {
            "status": "accepted" if accepted == report.imported else "partial",
            "format": report.format,
            "records_seen": report.records_seen,
            "events_parsed": report.imported,
            "events_queued": accepted,
            "issues": [
                {"record": issue.record, "code": issue.code}
                for issue in report.issues
            ],
        }

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
