"""Canonical, privacy-aware ShadowLens domain contracts (schema version 1.0)."""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    AIKind,
    CollectionState,
    EventSource,
    FieldState,
    FindingCategory,
    FindingStatus,
    RawVisibility,
    Severity,
    ToolKind,
    VisibilityTier,
)


class ContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ProcessMetadata(ContractModel):
    pid: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=256)
    exe: str | None = Field(default=None, max_length=2048)
    user: str | None = Field(default=None, max_length=256)
    cmdline_hash: str | None = Field(default=None, min_length=8, max_length=256)


class NetworkMetadata(ContractModel):
    dst_host: str | None = Field(default=None, max_length=253)
    dst_ip: str | None = Field(default=None, max_length=64)
    dst_port: int | None = Field(default=None, ge=1, le=65535)
    proto: Literal["tcp", "udp", "icmp", "other"] | None = None
    sni: str | None = Field(default=None, max_length=253)
    ja4: str | None = Field(default=None, max_length=256)
    bytes_out: int | None = Field(default=None, ge=0)
    bytes_in: int | None = Field(default=None, ge=0)
    direction: Literal["inbound", "outbound", "local", "unknown"] | None = None
    duration_ms: int | None = Field(default=None, ge=0)


class HTTPMetadata(ContractModel):
    method: str | None = Field(default=None, min_length=1, max_length=16)
    path: str | None = Field(default=None, max_length=2048)
    headers: dict[str, str] = Field(default_factory=dict)
    # This may reference an in-memory buffer, but is never part of serialized output.
    body_ref: object | None = Field(default=None, exclude=True, repr=False)
    stream: bool | None = None

    @field_validator("headers", mode="before")
    @classmethod
    def redact_sensitive_headers(cls, value: object) -> object:
        if not isinstance(value, dict):
            raise ValueError("headers must be a mapping")
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


class AIContext(ContractModel):
    provider: str | None = Field(default=None, max_length=128)
    kind: AIKind = AIKind.UNKNOWN
    model: str | None = Field(default=None, max_length=256)
    sanctioned: bool | None = None


class FieldProvenance(ContractModel):
    state: FieldState
    source: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def validate_provenance(self) -> "FieldProvenance":
        if self.state is FieldState.UNAVAILABLE and not self.note:
            raise ValueError("unavailable provenance requires a reason note")
        if self.state is not FieldState.UNAVAILABLE and not self.source:
            raise ValueError("observed or derived provenance requires a source")
        return self


class CollectionCoverage(ContractModel):
    adapter: EventSource
    state: CollectionState
    tiers_available: list[VisibilityTier] = Field(default_factory=list)
    checked_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=512)

    @field_validator("checked_at")
    @classmethod
    def require_aware_check_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("checked_at must be timezone-aware")
        return value


class Event(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    event_id: UUID = Field(default_factory=uuid4)
    ts: datetime
    source: EventSource
    tier: VisibilityTier
    host_id: str = Field(min_length=1, max_length=256)
    process: ProcessMetadata | None = None
    net: NetworkMetadata | None = None
    http: HTTPMetadata | None = None
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

    @model_validator(mode="after")
    def align_visibility(self) -> "Event":
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


class Evidence(ContractModel):
    masked: str = Field(min_length=1, max_length=2048)
    hmac: str | None = Field(default=None, max_length=256)
    offset: int | None = Field(default=None, ge=0)
    context_redacted: str | None = Field(default=None, max_length=4096)


class TriageAdvice(ContractModel):
    llm_verdict: str | None = Field(default=None, max_length=128)
    remediation: str | None = Field(default=None, max_length=2048)


class Finding(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    finding_id: UUID = Field(default_factory=uuid4)
    event_ids: list[UUID] = Field(min_length=1, max_length=256)
    category: FindingCategory
    rule_id: str = Field(min_length=2, max_length=64, pattern=r"^[A-Z0-9][A-Z0-9._-]+$")
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    tier: VisibilityTier
    evidence: Evidence
    mapped_controls: list[str] = Field(default_factory=list, max_length=64)
    status: FindingStatus = FindingStatus.OPEN
    triage: TriageAdvice | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now().astimezone())

    @field_validator("finding_id")
    @classmethod
    def require_uuid4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("finding_id must be a UUIDv4")
        return value

    @field_validator("event_ids")
    @classmethod
    def require_uuid4_event_links(cls, values: list[UUID]) -> list[UUID]:
        if any(value.version != 4 for value in values):
            raise ValueError("event_ids must contain UUIDv4 values")
        return values

    @field_validator("created_at")
    @classmethod
    def require_aware_created_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value


class AITool(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    tool_id: UUID = Field(default_factory=uuid4)
    host_id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    kind: ToolKind
    provider: str | None = Field(default=None, max_length=128)
    sanctioned: bool | None = None
    discovery: EventSource
    first_seen: datetime
    last_seen: datetime
    capabilities: list[str] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def validate_seen_range(self) -> "AITool":
        for value in (self.first_seen, self.last_seen):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("tool timestamps must be timezone-aware")
        if self.last_seen < self.first_seen:
            raise ValueError("last_seen cannot precede first_seen")
        return self
