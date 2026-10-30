"""HTTP-specific request contracts kept separate from transient collector contracts."""
from __future__ import annotations

from pydantic import Field, field_validator

from app.models.contracts import ContractModel, Event, FieldProvenance


class IngestHTTPMetadata(ContractModel):
    """HTTP metadata accepted by the API; deliberately has no body_ref field."""

    method: str | None = Field(default=None, min_length=1, max_length=16)
    path: str | None = Field(default=None, max_length=2048)
    headers: dict[str, str] = Field(default_factory=dict)
    stream: bool | None = None

    @field_validator("headers", mode="before")
    @classmethod
    def redact_and_bound_headers(cls, value: object) -> object:
        if not isinstance(value, dict):
            raise ValueError("headers must be a mapping")
        if len(value) > 64:
            raise ValueError("at most 64 HTTP headers may be ingested")
        sensitive_names = {
            "authorization",
            "proxy-authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "api-key",
            "x-auth-token",
            "x-goog-api-key",
            "x-amz-security-token",
        }
        safe: dict[str, str] = {}
        for name, header_value in value.items():
            if not isinstance(name, str) or not isinstance(header_value, str):
                raise ValueError("header names and values must be strings")
            if len(name) > 128:
                raise ValueError("HTTP header names may not exceed 128 characters")
            normalized = name.strip().lower()
            safe[name] = (
                "REDACTED"
                if (
                    normalized in sensitive_names
                    or "secret" in normalized
                    or normalized.endswith("-token")
                )
                else header_value[:1024]
            )
        return safe


class IngestEvent(Event):
    """Canonical event accepted over HTTP, excluding collector-only body handles."""

    http: IngestHTTPMetadata | None = None

    @field_validator("provenance")
    @classmethod
    def bound_provenance_fields(
        cls, value: dict[str, FieldProvenance]
    ) -> dict[str, FieldProvenance]:
        if len(value) > 64:
            raise ValueError("at most 64 provenance fields may be ingested")
        return value

    def to_event(self) -> Event:
        """Convert the transport-safe contract to the canonical internal contract."""
        return Event.model_validate(self.model_dump(mode="python"))
