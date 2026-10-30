"""Safe, metadata-only ingestion for HAR, mitmproxy JSON and JSONL exports.

Request/response bodies are deliberately never copied into canonical events,
diagnostics, logs, or persistence. This adapter emits T1 metadata events only.
"""
from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import PurePath
from typing import Any
from urllib.parse import urlsplit

from app.models.contracts import (
    AIContext,
    Event,
    FieldProvenance,
    HTTPMetadata,
    NetworkMetadata,
)
from app.models.enums import (
    EventSource,
    FieldState,
    RawVisibility,
    VisibilityTier,
)
from app.providers.registry import ProviderRegistry, Signal, default_registry

MAX_IMPORT_BYTES = 25 * 1024 * 1024
MAX_RECORDS = 10_000
MAX_LINE_BYTES = 1_048_576
SUPPORTED_SUFFIXES = {".har", ".json", ".jsonl", ".ndjson"}


class ImportValidationError(ValueError):
    """Safe-to-display import validation failure."""


@dataclass(frozen=True)
class ImportIssue:
    record: int
    code: str


@dataclass
class ImportReport:
    format: str
    events: list[Event] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)
    records_seen: int = 0

    @property
    def imported(self) -> int:
        return len(self.events)


def _timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # HAR/proxy timestamps may be Unix seconds or milliseconds.
        seconds = float(value) / 1000 if value > 10_000_000_000 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def _headers(value: Any) -> dict[str, str]:
    if isinstance(value, dict) and isinstance(value.get("fields"), list):
        value = value["fields"]
    if isinstance(value, dict):
        pairs = value.items()
    elif isinstance(value, list):
        pairs = (
            (item.get("name"), item.get("value"))
            if isinstance(item, dict)
            else (item[0], item[1])
            for item in value
            if isinstance(item, dict) or (isinstance(item, list) and len(item) >= 2)
        )
    else:
        return {}
    result: dict[str, str] = {}
    for name, content in pairs:
        if isinstance(name, str) and isinstance(content, (str, int, float)):
            result[name[:128]] = str(content)[:1024]
        if len(result) >= 64:
            break
    return result


def _request_parts(record: dict[str, Any], source_format: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    if source_format == "har":
        request = record.get("request") or {}
        if not isinstance(request, dict):
            raise ValueError("invalid_request")
        url = request.get("url")
        response = record.get("response") or {}
        started = record.get("startedDateTime")
        headers = request.get("headers")
        method = request.get("method")
        duration = record.get("time")
    elif source_format == "shadowlens":
        http = record.get("http") or {}
        net = record.get("net") or {}
        if not isinstance(http, dict) or not isinstance(net, dict):
            raise ValueError("invalid_shadowlens_record")
        host = net.get("dst_host") or record.get("host")
        scheme = http.get("scheme") or "https"
        port = net.get("dst_port") or (443 if scheme == "https" else 80)
        path = http.get("path") or "/"
        url = http.get("url")
        if not isinstance(url, str) and isinstance(host, str):
            url = f"{scheme}://{host}:{port}{path}"
        headers = http.get("headers")
        method = http.get("method")
        started = record.get("ts")
        response = {}
        duration = None
    elif source_format == "mitmproxy":
        request = record.get("request") or {}
        if not isinstance(request, dict):
            raise ValueError("invalid_request")
        scheme = request.get("scheme", "https")
        host = request.get("host")
        port = request.get("port")
        path = request.get("path", "/")
        if isinstance(host, str):
            safe_host = host
            default_port = 443 if scheme == "https" else 80
            url = f"{scheme}://{safe_host}:{port or default_port}{path}"
        else:
            url = None
        headers = request.get("headers")
        method = request.get("method")
        started = request.get("timestamp_start") or request.get("timestamp")
        response = record.get("response") or {}
        duration = None
    else:
        request = record
        url = record.get("url")
        request_line = record.get("request")
        method = record.get("method") or record.get("request_method")
        path = record.get("path") or record.get("uri") or record.get("request_uri") or "/"
        if isinstance(request_line, str):
            parts = request_line.split()
            if len(parts) >= 2:
                method = method or parts[0]
                if not record.get("request_uri") and not record.get("uri"):
                    path = parts[1]
        if not isinstance(url, str):
            host = record.get("host") or record.get("hostname") or record.get("server")
            scheme = record.get("scheme") or ("https" if record.get("ssl") else "http")
            port = record.get("port")
            if isinstance(host, str):
                default_port = 443 if scheme == "https" else 80
                url = f"{scheme}://{host}:{port or default_port}{path}"
        headers = record.get("headers") or record.get("request_headers")
        started = (
            record.get("ts") or record.get("timestamp") or record.get("@timestamp")
            or record.get("time") or record.get("startedDateTime")
        )
        response = record.get("response") or {}
        duration = record.get("duration")
    if not isinstance(url, str) or len(url) > 8192:
        raise ValueError("missing_or_invalid_url")
    if not isinstance(response, dict):
        response = {}
    metadata = {
        "method": method if isinstance(method, str) else None,
        "headers": _headers(headers),
        "timestamp": started,
        "status": response.get("status") or record.get("status"),
        "duration": duration,
    }
    return metadata, response, url


def _event_from_record(
    record: dict[str, Any],
    source_format: str,
    registry: ProviderRegistry,
) -> Event:
    metadata, _response, url = _request_parts(record, source_format)
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("invalid_url")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise ValueError("invalid_port") from exc
    path = parsed.path or "/"
    headers = metadata["headers"]
    user_agent = next(
        (value for name, value in headers.items() if name.lower() == "user-agent"),
        None,
    )
    classification = registry.classify(
        Signal(host=parsed.hostname, path=path, port=port, headers=headers, user_agent=user_agent)
    )
    ai = None
    if classification.provider != "unknown":
        ai = AIContext(
            provider=classification.provider,
            kind=classification.kind,
            model=None,
        )
    provenance = {
        "source_format": FieldProvenance(
            state=FieldState.OBSERVED, source=f"import:{source_format}"
        ),
        "http.method": FieldProvenance(
            state=FieldState.OBSERVED, source=f"import:{source_format}"
        ),
        "http.path": FieldProvenance(
            state=FieldState.OBSERVED, source=f"import:{source_format}"
        ),
        "net.dst_host": FieldProvenance(
            state=FieldState.OBSERVED, source=f"import:{source_format}"
        ),
        "ai.provider": FieldProvenance(
            state=FieldState.DERIVED,
            source="provider_registry",
            note="Metadata-only provider classification; not body inspection.",
        ),
    }
    return Event(
        ts=_timestamp(metadata["timestamp"]),
        source=EventSource.LOG,
        tier=VisibilityTier.T1,
        host_id="local-import",
        net=NetworkMetadata(
            dst_host=parsed.hostname.lower(),
            dst_port=port,
            proto="tcp",
            direction="outbound",
        ),
        http=HTTPMetadata(
            method=metadata["method"],
            path=path,
            headers=headers,
        ),
        ai=ai,
        raw_visibility=RawVisibility.METADATA,
        provenance=provenance,
    )


def _detect_format(filename: str, data: bytes) -> str:
    suffix = PurePath(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ImportValidationError("unsupported file type; use .har, .json or .jsonl")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportValidationError("import file must be UTF-8 text") from exc
    if not text.strip():
        raise ImportValidationError("import file is empty")
    first = text.lstrip()[0]
    if first not in "[{":
        raise ImportValidationError("import file is not valid JSON/JSONL")
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        if suffix == ".har":
            raise ImportValidationError("HAR file is malformed JSON") from None
        return "jsonl"
    if isinstance(parsed, dict) and isinstance(parsed.get("log"), dict):
        return "har"
    records = parsed.get("events") if isinstance(parsed, dict) else parsed
    if isinstance(records, list) and records and all(
        isinstance(item, dict) and "request" in item for item in records[:3]
    ):
        return "mitmproxy"
    if isinstance(records, list) and records and all(
        isinstance(item, dict) and ("http" in item or "net" in item)
        for item in records[:3]
    ):
        return "shadowlens"
    if isinstance(parsed, dict) and isinstance(parsed.get("http"), dict):
        return "shadowlens"
    if suffix == ".har":
        raise ImportValidationError("file does not contain a HAR log")
    return "json"


def parse_log_bytes(
    filename: str,
    data: bytes,
    *,
    registry: ProviderRegistry | None = None,
) -> ImportReport:
    """Parse supported exports into T1 events without retaining body content."""
    if len(data) > MAX_IMPORT_BYTES:
        raise ImportValidationError("import exceeds the 25 MiB size limit")
    source_format = _detect_format(filename, data)
    active_registry = registry or default_registry()
    text = data.decode("utf-8-sig")
    if source_format == "jsonl":
        raw_records: list[Any] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if len(line.encode("utf-8")) > MAX_LINE_BYTES:
                raw_records.append((line_number, None))
                continue
            if not line.strip():
                continue
            try:
                raw_records.append((line_number, json.loads(line)))
            except json.JSONDecodeError:
                raw_records.append((line_number, None))
    else:
        parsed = json.loads(text)
        if source_format == "har":
            entries = parsed.get("log", {}).get("entries", [])
            if not isinstance(entries, list):
                raise ImportValidationError("HAR log.entries must be an array")
            raw_records = list(enumerate(entries, start=1))
        elif source_format in {"mitmproxy", "shadowlens"}:
            records = parsed.get("events", []) if isinstance(parsed, dict) else parsed
            if not isinstance(records, list):
                raise ImportValidationError("ShadowLens events must be an array")
            raw_records = list(enumerate(records, start=1))
        elif isinstance(parsed, list):
            raw_records = list(enumerate(parsed, start=1))
        elif isinstance(parsed, dict):
            raw_records = [(1, parsed)]
        else:
            raise ImportValidationError("JSON export must contain an object or array")
    if len(raw_records) > MAX_RECORDS:
        raise ImportValidationError("import exceeds the 10,000 record limit")

    report = ImportReport(format=source_format)
    for record_number, raw_record in raw_records:
        report.records_seen += 1
        if not isinstance(raw_record, dict):
            report.issues.append(ImportIssue(record=record_number, code="malformed_record"))
            continue
        try:
            event = _event_from_record(raw_record, source_format, active_registry)
        except (ValueError, TypeError, KeyError, OverflowError):
            report.issues.append(ImportIssue(record=record_number, code="invalid_http_record"))
            continue
        report.events.append(event)
    return report
