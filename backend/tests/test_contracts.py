from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.contracts import (
    AIKind,
    AITool,
    CollectionCoverage,
    CollectionState,
    Event,
    EventSource,
    Evidence,
    FieldProvenance,
    FieldState,
    Finding,
    FindingCategory,
    FindingStatus,
    HTTPMetadata,
    NetworkMetadata,
    ProcessMetadata,
    RawVisibility,
    Severity,
    ToolKind,
    VisibilityTier,
)


def event_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_id": str(uuid4()),
        "ts": "2026-10-30T10:15:22.123Z",
        "source": "socket",
        "tier": "T1",
        "host_id": "sha256:host-fingerprint",
        "process": {"pid": 4242, "name": "Cursor", "cmdline_hash": "sha256:command"},
        "net": {
            "dst_host": "api.openai.com",
            "dst_port": 443,
            "proto": "tcp",
            "direction": "outbound",
            "bytes_out": 1024,
            "bytes_in": 2048,
        },
        "http": {
            "method": "POST",
            "path": "/v1/chat/completions",
            "headers": {"content-type": "application/json", "authorization": "Bearer do-not-store"},
            "body_ref": "transient-buffer-123",
            "stream": True,
        },
        "ai": {"provider": "openai", "kind": "cloud", "model": "gpt-4o", "sanctioned": False},
        "raw_visibility": "metadata",
    }
    payload.update(overrides)
    return payload


def finding_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "finding_id": str(uuid4()),
        "event_ids": [str(uuid4())],
        "category": "secret",
        "rule_id": "SEC-AWS-ACCESS-KEY",
        "severity": "high",
        "confidence": 0.91,
        "tier": "T3",
        "evidence": {
            "masked": "AKIA************MPLE",
            "hmac": "hmac-sha256:example",
            "offset": 412,
            "context_redacted": "aws_access_key_id = AKIA****",
        },
        "mapped_controls": ["NIST-AI-RMF:MANAGE-2.3"],
        "status": "open",
    }
    payload.update(overrides)
    return payload


def test_event_accepts_canonical_metadata_and_timezone() -> None:
    event = Event.model_validate(event_payload())
    assert event.source is EventSource.SOCKET
    assert event.tier is VisibilityTier.T1
    assert event.ts.utcoffset() == UTC.utcoffset(event.ts)


def test_event_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        Event.model_validate(event_payload(ts="2026-10-30T10:15:22"))


@pytest.mark.parametrize(
    ("tier", "raw_visibility"),
    [("T1", "content"), ("T2", "metadata"), ("T3", "shape")],
)
def test_event_rejects_inconsistent_visibility(tier: str, raw_visibility: str) -> None:
    with pytest.raises(ValidationError, match="raw_visibility"):
        Event.model_validate(event_payload(tier=tier, raw_visibility=raw_visibility))


def test_event_rejects_unknown_fields_and_invalid_network_values() -> None:
    with pytest.raises(ValidationError):
        Event.model_validate(event_payload(unreviewed_field=True))
    with pytest.raises(ValidationError):
        Event.model_validate(event_payload(net={"dst_port": 70000}))


def test_transient_body_reference_is_never_serialized() -> None:
    event = Event.model_validate(event_payload())
    assert event.http is not None
    assert event.http.body_ref == "transient-buffer-123"
    dumped = event.model_dump(mode="json")
    assert "body_ref" not in dumped["http"]
    assert "do-not-store" not in str(dumped)
    assert "transient-buffer-123" not in event.model_dump_json()


def test_sensitive_http_headers_are_redacted_at_contract_boundary() -> None:
    event = Event.model_validate(event_payload())
    assert event.http is not None
    assert event.http.headers["authorization"] == "REDACTED"
    assert event.http.headers["content-type"] == "application/json"


def test_tier_and_raw_visibility_are_not_interchangeable() -> None:
    t2 = Event.model_validate(event_payload(tier="T2", raw_visibility="shape"))
    assert t2.tier is VisibilityTier.T2
    assert t2.raw_visibility is RawVisibility.SHAPE


def test_finding_requires_at_least_one_linked_event() -> None:
    with pytest.raises(ValidationError):
        Finding.model_validate(finding_payload(event_ids=[]))


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_finding_confidence_is_bounded(confidence: float) -> None:
    with pytest.raises(ValidationError):
        Finding.model_validate(finding_payload(confidence=confidence))


def test_finding_evidence_is_bounded_and_redacted_shape_is_explicit() -> None:
    finding = Finding.model_validate(finding_payload())
    assert finding.evidence.masked == "AKIA************MPLE"
    with pytest.raises(ValidationError):
        Evidence.model_validate({"masked": "x" * 5000})


def test_provenance_distinguishes_derived_and_unavailable() -> None:
    derived = FieldProvenance(state=FieldState.DERIVED, source="flow-shape-window")
    unavailable = FieldProvenance(state=FieldState.UNAVAILABLE, note="OS permission denied")
    assert derived.state is FieldState.DERIVED
    assert unavailable.state is FieldState.UNAVAILABLE
    with pytest.raises(ValidationError):
        FieldProvenance(state=FieldState.UNAVAILABLE)


def test_tool_and_collection_coverage_contracts() -> None:
    tool = AITool(
        name="Ollama",
        kind=ToolKind.LOCAL_LLM,
        provider="ollama",
        host_id="sha256:host",
        discovery=EventSource.SOCKET,
        first_seen=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )
    coverage = CollectionCoverage(
        adapter=EventSource.SOCKET,
        state=CollectionState.PARTIAL,
        tiers_available=[VisibilityTier.T1],
        checked_at=datetime.now(UTC),
        reason="Some process metadata is permission-limited",
    )
    assert tool.kind is ToolKind.LOCAL_LLM
    assert coverage.state is CollectionState.PARTIAL
    assert AIKind.CLOUD.value == "cloud"
    assert FindingCategory.SECRET.value == "secret"
    assert Severity.HIGH.value == "high"
    assert FindingStatus.OPEN.value == "open"
