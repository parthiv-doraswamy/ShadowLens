"""HTTP-specific request contracts kept separate from transient collector contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from app.models.contracts import (
    AIContext,
    CollectionCoverage,
    ContractModel,
    Event,
    FieldProvenance,
    NetworkMetadata,
    ProcessMetadata,
)
from app.models.enums import RawVisibility, VisibilityTier, EventSource


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


class IngestEvent(ContractModel):
    """Canonical HTTP event contract without collector-only transient body handles."""

    schema_version: Literal["1.0"] = "1.0"
    event_id: UUID = Field(default_factory=uuid4)
    ts: datetime
    source: EventSource
    tier: VisibilityTier
    host_id: str = Field(min_length=1, max_length=256)
    process: ProcessMetadata | None = None
    net: NetworkMetadata | None = None
    http: IngestHTTPMetadata | None = None
    ai: AIContext | None = None
    raw_visibility: RawVisibility
    provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
    collection_status: CollectionCoverage | None = None

    @field_validator("event_id")
    @classmethod
    def require_uuid4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("event_id must be a UUIDv4")
        return value

    @field_validator("ts")
    @classmethod
    def require_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("ts must be timezone-aware")
        return value

    @field_validator("provenance")
    @classmethod
    def bound_provenance_fields(
        cls, value: dict[str, FieldProvenance]
    ) -> dict[str, FieldProvenance]:
        if len(value) > 64:
            raise ValueError("at most 64 provenance fields may be ingested")
        return value

    @model_validator(mode="after")
    def align_visibility(self) -> IngestEvent:
        expected = {
            VisibilityTier.T1: RawVisibility.METADATA,
            VisibilityTier.T2: RawVisibility.SHAPE,
            VisibilityTier.T3: RawVisibility.CONTENT,
        }[self.tier]
        if self.raw_visibility is not expected:
            raise ValueError(
                f"raw_visibility must be '{expected.value}' for tier {self.tier.value}"
            )
        return self

    def to_event(self) -> Event:
        """Convert the transport-safe contract to the canonical internal contract."""
        return Event.model_validate(self.model_dump(mode="python"))
