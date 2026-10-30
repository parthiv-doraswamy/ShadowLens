from __future__ import annotations

import asyncio
import json
import os
import stat
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.bus.event_bus import EventPublisher
from app.main import create_app
from app.observability import configure_structured_logging
from app.persistence import EventRow


def make_payload() -> dict[str, object]:
    return {
        "event_id": str(uuid4()),
        "ts": datetime.now(UTC).isoformat(),
        "source": "socket",
        "tier": "T1",
        "host_id": "host-hash-test",
        "raw_visibility": "metadata",
        "net": {"dst_host": "api.example.test", "dst_port": 443, "proto": "tcp"},
        "http": {
            "method": "POST",
            "path": "/v1/chat/completions",
            "headers": {"Authorization": "Bearer example-sensitive-value"},
        },
    }


def wait_for_persisted_event(app: object, event_id: str) -> EventRow:
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        with Session(app.state.database_engine) as session:  # type: ignore[attr-defined]
            row = session.get(EventRow, event_id)
            if row is not None:
                return row
        time.sleep(0.01)
    raise AssertionError("event was accepted but not persisted before timeout")


def test_ingest_requires_bearer_and_persists_redacted_event(tmp_path: Path) -> None:
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'ingest.db'}",
        token_path=tmp_path / "access.token",
    )
    payload = make_payload()
    event_id = str(payload["event_id"])

    with TestClient(app) as client:
        unauthorized = client.post("/api/events", json=payload)
        assert unauthorized.status_code == 401

        response = client.post(
            "/api/events",
            json=payload,
            headers={"Authorization": f"Bearer {app.state.api_token}"},
        )
        assert response.status_code == 202
        assert response.json() == {"status": "accepted", "event_id": event_id}

        row = wait_for_persisted_event(app, event_id)
        assert "example-sensitive-value" not in row.meta_json
        assert "REDACTED" in row.meta_json
        assert json.loads(row.meta_json)["http"]["headers"]["Authorization"] == "REDACTED"


def test_http_ingest_rejects_transient_body_reference(tmp_path: Path) -> None:
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'body-ref.db'}",
        token_path=tmp_path / "access.token",
    )
    payload = make_payload()
    http = payload["http"]
    assert isinstance(http, dict)
    http["body_ref"] = "synthetic-raw-body-secret"

    with TestClient(app) as client:
        response = client.post(
            "/api/events",
            json=payload,
            headers={"Authorization": f"Bearer {app.state.api_token}"},
        )
        assert response.status_code == 422
        assert "synthetic-raw-body-secret" not in response.text
        assert '"input"' not in response.text
        with Session(app.state.database_engine) as session:
            assert session.get(EventRow, str(payload["event_id"])) is None


def test_docs_and_openapi_are_protected(tmp_path: Path) -> None:
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'docs.db'}",
        token_path=tmp_path / "access.token",
    )
    with TestClient(app) as client:
        assert client.get("/api/docs").status_code == 401
        assert client.get("/api/openapi.json").status_code == 401
        headers = {"Authorization": f"Bearer {app.state.api_token}"}
        assert client.get("/api/docs", headers=headers).status_code == 200
        schema = client.get("/api/openapi.json", headers=headers)
        assert schema.status_code == 200
        assert "/api/events" in schema.json()["paths"]


def test_token_file_is_owner_only_and_stable_across_restarts(tmp_path: Path) -> None:
    token_path = tmp_path / "secrets" / "access.token"
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'token.db'}",
        token_path=token_path,
    )
    with TestClient(app):
        first_token = app.state.api_token
        assert len(first_token) >= 32
        assert token_path.read_text(encoding="utf-8").strip() == first_token
        if os.name != "nt":
            assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
            assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700

    second_app = create_app(
        database_url=f"sqlite:///{tmp_path / 'token.db'}",
        token_path=token_path,
    )
    with TestClient(second_app):
        assert second_app.state.api_token == first_token


def test_shutdown_stops_collectors_then_drains_accepted_events(tmp_path: Path) -> None:
    class OneEventCollector:
        async def run(
            self, publish: EventPublisher, stop_event: asyncio.Event
        ) -> None:
            from app.api_schemas import IngestEvent

            await publish(IngestEvent.model_validate(make_payload()).to_event())
            await stop_event.wait()

    database_path = tmp_path / "shutdown.db"
    app = create_app(
        database_url=f"sqlite:///{database_path}",
        token_path=tmp_path / "shutdown.token",
        collectors={"one-event": OneEventCollector()},
    )

    with TestClient(app) as client:
        deadline = time.monotonic() + 2.0
        while app.state.event_bus.stats().accepted < 1 and time.monotonic() < deadline:
            time.sleep(0.01)
        health = client.get("/api/health").json()
        assert health["collectors"]["status"] == "running"
        assert health["event_bus"]["accepted"] == 1

    from app.persistence import create_database_engine, initialize_database

    engine = create_database_engine(f"sqlite:///{database_path}")
    try:
        initialize_database(engine)
        with Session(engine) as session:
            assert session.exec(select(EventRow)).first() is not None
    finally:
        engine.dispose()


def test_token_creation_does_not_change_existing_parent_permissions(tmp_path: Path) -> None:
    parent = tmp_path / "shared-directory"
    parent.mkdir()
    if os.name != "nt":
        parent.chmod(0o755)
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'existing-parent.db'}",
        token_path=parent / "access.token",
    )
    with TestClient(app):
        assert (parent / "access.token").is_file()
        if os.name != "nt":
            assert stat.S_IMODE(parent.stat().st_mode) == 0o755


def test_http_logs_are_json_and_exclude_query_headers_and_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_structured_logging("INFO")
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'access-log.db'}",
        token_path=tmp_path / "access-log.token",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/health?access_token=query-secret-value",
            headers={"Authorization": "Bearer header-secret-value"},
        )
        assert response.status_code == 200
        request_id = response.headers["X-Request-ID"]

    output = capsys.readouterr().err
    assert "query-secret-value" not in output
    assert "header-secret-value" not in output
    records = [json.loads(line) for line in output.splitlines() if line.strip()]
    access = next(record for record in records if record["event"] == "http_request_completed")
    assert access["route"] == "/api/health"
    assert access["method"] == "GET"
    assert access["status_code"] == 200
    assert access["request_id"] == request_id
    assert "query" not in access
    assert "headers" not in access
    assert "body" not in access


def test_unhandled_error_returns_generic_response_and_safe_log(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    configure_structured_logging("INFO")
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'internal-error.db'}",
        token_path=tmp_path / "internal-error.token",
    )

    @app.get("/api/test-failure")
    async def fail_request() -> None:
        raise RuntimeError("sensitive internal error text")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/test-failure")
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
        assert response.headers.get("X-Request-ID")

    output = capsys.readouterr().err
    assert "sensitive internal error text" not in output
    assert "http_request_failed" in output
    assert "RuntimeError" in output


def test_cors_allows_only_configured_local_frontend(tmp_path: Path) -> None:
    from app.config import Settings

    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "cors",
        cors_origins="http://localhost:5173",
    )
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'cors.db'}",
        token_path=tmp_path / "cors.token",
        settings=settings,
    )
    with TestClient(app) as client:
        allowed = client.options(
            "/api/events",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "access-control-allow-credentials" not in allowed.headers

        rejected = client.options(
            "/api/events",
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in rejected.headers
