"""Structured JSON logging with conservative secret and payload redaction."""
from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog

SENSITIVE_KEY_PARTS = (
    "authorization", "cookie", "password", "passwd", "secret",
    "api_key", "apikey", "access_token", "refresh_token", "token",
    "prompt", "body", "payload", "content", "raw",
)
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+\S+")
_OPENAI_KEY_PATTERN = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{8,}\b")
_AWS_KEY_PATTERN = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|prompt)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
_QUERY_SECRET_PATTERN = re.compile(
    r"(?i)([?&](?:token|api_key|key|password|secret|authorization|code)=)[^&\s]+"
)
_MAX_STRING_LENGTH = 512
_MAX_COLLECTION_ITEMS = 32
_MAX_NESTING = 4


def _sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _sanitize_string(value: str) -> str:
    """Remove common credential patterns and bound arbitrary log strings."""
    sanitized = _BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    sanitized = _OPENAI_KEY_PATTERN.sub("[REDACTED_API_KEY]", sanitized)
    sanitized = _AWS_KEY_PATTERN.sub("[REDACTED_AWS_KEY]", sanitized)
    sanitized = _SECRET_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}=[REDACTED]", sanitized
    )
    sanitized = _QUERY_SECRET_PATTERN.sub(
        lambda match: f"{match.group(1)}[REDACTED]", sanitized
    )
    if len(sanitized) > _MAX_STRING_LENGTH:
        sanitized = sanitized[:_MAX_STRING_LENGTH] + "…"
    return sanitized


def sanitize_log_value(value: object, *, depth: int = 0) -> object:
    """Convert values to bounded JSON-safe data without object repr leakage."""
    if depth > _MAX_NESTING:
        return "[TRUNCATED]"
    if isinstance(value, str):
        return _sanitize_string(value)
    if isinstance(value, bytes | bytearray | memoryview):
        return "[REDACTED_BYTES]"
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= _MAX_COLLECTION_ITEMS:
                safe["_truncated"] = True
                break
            safe_key = str(key)[:128]
            safe[safe_key] = (
                "[REDACTED]"
                if _sensitive_key(safe_key)
                else sanitize_log_value(item, depth=depth + 1)
            )
        return safe
    if isinstance(value, list | tuple):
        safe_items = [
            sanitize_log_value(item, depth=depth + 1)
            for item in value[:_MAX_COLLECTION_ITEMS]
        ]
        if len(value) > _MAX_COLLECTION_ITEMS:
            safe_items.append("[TRUNCATED]")
        return safe_items
    if value is None or isinstance(value, bool | int | float):
        return value
    return f"<{type(value).__name__}>"


def redact_log_fields(
    _logger: Any,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that redacts risky field names and sanitizes values."""
    safe: dict[str, Any] = {}
    for key, value in event_dict.items():
        safe_key = str(key)[:128]
        safe[safe_key] = (
            "[REDACTED]"
            if _sensitive_key(safe_key)
            else sanitize_log_value(value)
        )
    return safe


def configure_structured_logging(level_name: str | None = None) -> None:
    """Configure redacted JSON application logs and disable unsafe access lines."""
    name = (level_name or "INFO").strip().upper()
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    if name not in levels:
        raise ValueError("SHADOWLENS_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")

    # Uvicorn's default access log includes the raw request target and query string.
    logging.getLogger("uvicorn.access").disabled = True
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            redact_log_fields,
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(levels[name]),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> Any:
    """Return a logger after the application has configured structlog."""
    return structlog.get_logger(name)


# Collector/bus tests may use these modules without constructing the FastAPI app.
configure_structured_logging()
