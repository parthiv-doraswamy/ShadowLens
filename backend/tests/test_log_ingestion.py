"""Security and correctness tests for metadata-only HAR/JSONL ingestion."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.ingestion.logs import (
    MAX_IMPORT_BYTES,
    ImportValidationError,
    parse_log_bytes,
)
from app.main import create_app


def har_bytes(entries: list[dict[str, object]]) -> bytes:
    return json.dumps({"log": {"version": "1.2", "entries": entries}}).encode()


def har_entry(url: str = "https://api.openai.com/v1/chat/completions") -> dict[str, object]:
    return {
        "startedDateTime": "2026-10-31T10:00:00Z",
        "request": {
            "method": "POST",
            "url": url,
            "headers": [
                {"name": "Authorization", "value": "Bearer super-secret-token"},
                {"name": "Content-Type", "value": "application/json"},
            ],
            "postData": {"text": "AWS_SECRET_ACCESS_KEY=very-secret-body-value"},
        },
        "response": {
            "status": 200,
            "content": {"text": "response-body-must-not-be-retained"},
        },
        "time": 12.5,
    }


def test_har_import_emits_metadata_and_never_retains_bodies_or_secrets() -> None:
    report = parse_log_bytes("capture.har", har_bytes([har_entry()]))
    assert report.format == "har"
    assert report.records_seen == 1
    assert report.imported == 1
    event = report.events[0]
    assert event.source.value == "log"
    assert event.tier.value == "T1"
    assert event.ai is not None and event.ai.provider == "openai"
    serialized = event.model_dump_json()
    assert "very-secret-body-value" not in serialized
    assert "response-body-must-not-be-retained" not in serialized
    assert "super-secret-token" not in serialized
    assert event.http is not None
    assert event.http.headers["Authorization"] == "REDACTED"


def test_har_import_continues_after_malformed_record() -> None:
    report = parse_log_bytes(
        "capture.har",
        har_bytes([{"request": "not-an-object"}, har_entry(), {"request": {}}]),
    )
    assert report.imported == 1
    assert report.records_seen == 3
    assert len(report.issues) == 2
    assert report.issues[0].code == "invalid_http_record"


def test_mitmproxy_json_dump_is_detected_and_parsed() -> None:
    payload = [{
        "type": "http",
        "request": {
            "scheme": "https",
            "host": "api.anthropic.com",
            "port": 443,
            "path": "/v1/messages",
            "method": "POST",
            "headers": {
                "__class__": "Headers",
                "fields": [["anthropic-version", "2023-06-01"], ["x-api-key", "sk-ant-secret"]],
            },
            "content": "never-persist-this",
        },
        "response": {"status_code": 200, "content": "also-private"},
    }]
    report = parse_log_bytes("mitm.json", json.dumps(payload).encode())
    assert report.format == "mitmproxy"
    assert report.imported == 1
    event = report.events[0]
    assert event.ai is not None and event.ai.provider == "anthropic"
    assert "never-persist-this" not in event.model_dump_json()
    assert "sk-ant-secret" not in event.model_dump_json()


def test_nginx_style_jsonl_and_mock_log_are_supported() -> None:
    nginx = {
        "time": "2026-10-31T10:00:00Z",
        "host": "api.openai.com",
        "request": "POST /v1/chat/completions HTTP/1.1",
        "status": 200,
        "request_headers": {"Authorization": "Bearer secret"},
    }
    report = parse_log_bytes("access.jsonl", (json.dumps(nginx) + "\n").encode())
    assert report.format == "jsonl"
    assert report.imported == 1
    assert report.events[0].http is not None
    assert report.events[0].http.method == "POST"
    assert report.events[0].http.path == "/v1/chat/completions"

    mock = {"ts": "2026-10-31T10:00:00Z", "url": "http://localhost:11434/api/chat"}
    mock_report = parse_log_bytes("mock.json", json.dumps(mock).encode())
    assert mock_report.format == "json"
    assert mock_report.imported == 1
    assert mock_report.events[0].net is not None
    assert mock_report.events[0].net.dst_port == 11434


@pytest.mark.parametrize(
    ("filename", "data"),
    [
        ("bad.exe", b"{}"),
        ("empty.har", b"  "),
        ("broken.har", b'{"log":'),
        ("not-a-har.har", b'{"entries": []}'),
    ],
)
def test_invalid_type_empty_and_malformed_files_are_rejected(
    filename: str, data: bytes
) -> None:
    with pytest.raises(ImportValidationError):
        parse_log_bytes(filename, data)


def test_oversized_file_is_rejected_before_parsing() -> None:
    with pytest.raises(ImportValidationError, match="25 MiB"):
        parse_log_bytes("large.jsonl", b" " * (MAX_IMPORT_BYTES + 1))


def test_jsonl_reports_bad_lines_without_stopping_following_records() -> None:
    good = json.dumps({"url": "https://api.openai.com/v1/models"})
    report = parse_log_bytes("events.jsonl", (good + "\n{broken\n" + good).encode())
    assert report.records_seen == 3
    assert report.imported == 2
    assert len(report.issues) == 1
    assert report.issues[0].code == "malformed_record"


def test_authenticated_multipart_api_queues_metadata_only(tmp_path) -> None:
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'ingest.db'}",
        token_path=tmp_path / "access.token",
    )
    with TestClient(app) as client:
        token = app.state.api_token
        payload = har_bytes([har_entry()])
        denied = client.post("/api/ingest", files={"file": ("capture.har", payload)})
        assert denied.status_code == 401
        response = client.post(
            "/api/ingest",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("capture.har", payload, "application/json")},
        )
        assert response.status_code == 202
        body = response.json()
        assert body["events_parsed"] == 1
        assert body["events_queued"] == 1
        assert body["format"] == "har"
