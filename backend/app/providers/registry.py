"""Deterministic provider classification from observable request metadata.

The registry intentionally never inspects request bodies. Unknown API-like
requests remain provisional and cannot be promoted by a URL path alone.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import AIKind


class Signal(BaseModel):
    """One optional observable signal used for provider classification."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    host: str | None = Field(default=None, max_length=253)
    path: str | None = Field(default=None, max_length=2048)
    port: int | None = Field(default=None, ge=1, le=65535)
    sni: str | None = Field(default=None, max_length=253)
    headers: dict[str, str] = Field(default_factory=dict, max_length=64, repr=False, exclude=True)
    user_agent: str | None = Field(default=None, max_length=512)
    # Keys only, extracted by an upstream bounded parser; values/body are never retained.
    json_keys: list[str] = Field(default_factory=list, max_length=64)

    @field_validator("host", "sni")
    @classmethod
    def normalize_hostname(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().rstrip(".").lower()
        if not normalized or any(char.isspace() for char in normalized):
            raise ValueError("hostname must be a non-empty host value")
        if len(normalized) > 253:
            raise ValueError("hostname is too long")
        return normalized

    @field_validator("headers")
    @classmethod
    def normalize_headers(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for name, item in value.items():
            if not isinstance(name, str) or not isinstance(item, str):
                raise ValueError("header names and values must be strings")
            normalized[name.strip().lower()] = item[:512]
        return normalized

    @field_validator("json_keys")
    @classmethod
    def normalize_json_keys(cls, values: list[str]) -> list[str]:
        return [value.strip().lower()[:64] for value in values if isinstance(value, str)]

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        user_agent: str | None = None,
        sni: str | None = None,
    ) -> Signal:
        """Build metadata signals from a URL without requesting or resolving it."""
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("URL must be an absolute HTTP(S) URL")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("URL contains an invalid port") from exc
        effective_port = port or (443 if parsed.scheme == "https" else 80)
        return cls(
            host=parsed.hostname,
            path=parsed.path or "/",
            port=effective_port,
            headers=headers or {},
            user_agent=user_agent,
            sni=sni,
        )


class ProviderDefinition(BaseModel):
    """Validated declarative signature for one provider."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    display_name: str = Field(min_length=1, max_length=100)
    kind: AIKind
    hosts: list[str] = Field(default_factory=list, max_length=64)
    paths: list[str] = Field(default_factory=list, max_length=64)
    ports: list[int] = Field(default_factory=list, max_length=32)
    sni: list[str] = Field(default_factory=list, max_length=64)
    headers: dict[str, str] = Field(default_factory=dict, max_length=32)
    user_agents: list[str] = Field(default_factory=list, max_length=32)
    min_score: int = Field(default=3, ge=1, le=20)

    @field_validator("hosts", "sni")
    @classmethod
    def normalize_patterns(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            item = value.strip().rstrip(".").lower()
            if not item or len(item) > 253:
                raise ValueError("host patterns must be non-empty and <=253 characters")
            result.append(item)
        return result

    @field_validator("headers")
    @classmethod
    def normalize_header_patterns(cls, values: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for name, pattern in values.items():
            normalized_name = name.strip().lower()
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(
                    f"invalid header fingerprint pattern for {normalized_name}"
                ) from exc
            normalized[normalized_name] = pattern
        return normalized


@dataclass(frozen=True)
class MatchEvidence:
    """Safe explanation of a matched signature; never includes header values."""

    signal: str
    detail: str


@dataclass(frozen=True)
class ClassificationResult:
    provider: str
    display_name: str
    kind: str
    confidence: float
    matched: bool
    provisional: bool
    evidence: tuple[MatchEvidence, ...] = field(default_factory=tuple)

    def to_ai_context(
        self, *, model: str | None = None, sanctioned: bool | None = None
    ) -> dict[str, Any]:
        """Return a payload compatible with the existing AIContext contract."""
        return {
            "provider": self.provider,
            "kind": self.kind,
            "model": model,
            "sanctioned": sanctioned,
        }


def _host_matches(host: str | None, pattern: str) -> bool:
    if host is None:
        return False
    # Match wildcard labels independently: '*.example.com' cannot match
    # 'notexample.com', and the AWS region wildcard is supported as well.
    host_labels = host.split(".")
    pattern_labels = pattern.split(".")
    if len(host_labels) != len(pattern_labels):
        return False
    return all(
        fnmatch.fnmatchcase(label, pattern_label)
        for label, pattern_label in zip(host_labels, pattern_labels, strict=True)
    )


def _path_matches(path: str | None, pattern: str) -> bool:
    return path is not None and fnmatch.fnmatchcase(path.lower(), pattern.lower())


def _safe_header_value(value: str) -> str:
    """Bound values before signature matching and never return them as evidence."""
    return value[:512]


class ProviderRegistry:
    """Immutable-in-use, reloadable provider registry backed by YAML."""

    def __init__(self, providers: list[ProviderDefinition]) -> None:
        ids = [provider.id for provider in providers]
        if len(ids) != len(set(ids)):
            raise ValueError("provider registry contains duplicate provider IDs")
        self._providers = tuple(providers)

    @property
    def providers(self) -> tuple[ProviderDefinition, ...]:
        return self._providers

    @classmethod
    def from_yaml(cls, path: str | Path) -> ProviderRegistry:
        """Load and validate the complete registry before replacing live state."""
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or set(raw) != {"version", "providers"}:
            raise ValueError("provider YAML must contain only version and providers")
        if raw["version"] != 1 or not isinstance(raw["providers"], list):
            raise ValueError("unsupported provider registry format")
        providers = [ProviderDefinition.model_validate(item) for item in raw["providers"]]
        return cls(providers)

    def reload(self, path: str | Path) -> None:
        """Atomically replace registry contents after successful validation."""
        replacement = self.from_yaml(path)
        self._providers = replacement._providers

    def classify(self, signal: Signal) -> ClassificationResult:
        scored: list[tuple[int, ProviderDefinition, tuple[MatchEvidence, ...]]] = []
        for provider in self._providers:
            score = 0
            evidence: list[MatchEvidence] = []
            if any(_host_matches(signal.host, pattern) for pattern in provider.hosts):
                score += 4
                evidence.append(
                    MatchEvidence("host", "destination host matched provider signature")
                )
            if any(_host_matches(signal.sni, pattern) for pattern in provider.sni):
                score += 4
                evidence.append(
                    MatchEvidence("sni", "TLS SNI matched provider signature")
                )
            matching_paths = [
                pattern for pattern in provider.paths
                if _path_matches(signal.path, pattern)
            ]
            if matching_paths:
                score += 1
                evidence.append(
                    MatchEvidence("path", "request path matched provider signature")
                )
            if signal.port is not None and signal.port in provider.ports:
                score += 1
                evidence.append(
                    MatchEvidence("port", "destination port matched provider signature")
                )
            for header_name, pattern in provider.headers.items():
                value = signal.headers.get(header_name)
                if value is not None and re.search(
                    pattern, _safe_header_value(value), re.IGNORECASE
                ):
                    score += 3
                    evidence.append(
                        MatchEvidence("header", f"{header_name} matched provider signature")
                    )
            if provider.user_agents and signal.user_agent:
                if any(
                    token.lower() in signal.user_agent.lower()
                    for token in provider.user_agents
                ):
                    score += 2
                    evidence.append(
                        MatchEvidence("user_agent", "User-Agent matched provider signature")
                    )
            if score >= provider.min_score:
                scored.append((score, provider, tuple(evidence)))

        if scored:
            scored.sort(key=lambda item: (item[0], item[1].id), reverse=True)
            _, best, best_evidence = scored[0]
            # A concrete host/SNI match is strong; corroborated non-host signals
            # can classify only when at least two independent signal families match.
            strong_host = any(item.signal in {"host", "sni"} for item in best_evidence)
            confidence = 0.99 if strong_host else min(0.85, 0.60 + 0.05 * len(best_evidence))
            return ClassificationResult(
                provider=best.id,
                display_name=best.display_name,
                kind=best.kind.value,
                confidence=confidence,
                matched=True,
                provisional=False,
                evidence=best_evidence,
            )

        api_like_path = bool(signal.path and signal.path.lower() in {
            "/v1/chat/completions", "/v1/messages", "/chat/completions"
        })
        # Only key names supplied by a bounded upstream JSON parser are used.
        # Payload values and raw body contents are deliberately not part of Signal.
        api_like_shape = bool({"messages", "prompt"} & set(signal.json_keys))
        api_like = api_like_path or api_like_shape
        if api_like:
            return ClassificationResult(
                provider="unknown_llm_api",
                display_name="Unknown LLM-like API",
                kind="unknown_llm_api",
                confidence=0.7,
                matched=False,
                provisional=True,
                evidence=(
                    MatchEvidence(
                        "path" if api_like_path else "json_keys",
                        "LLM-like request shape; provider identity is unconfirmed",
                    ),
                ),
            )

        return ClassificationResult(
            provider="unknown",
            display_name="Unknown destination",
            kind=AIKind.UNKNOWN.value,
            confidence=0.0,
            matched=False,
            provisional=True,
            evidence=(),
        )


def default_registry() -> ProviderRegistry:
    """Load the checked-in provider registry relative to the package root."""
    registry_path = Path(__file__).with_name("providers.yaml")
    return ProviderRegistry.from_yaml(registry_path)


def classify_request(
    signal: Signal,
    registry: ProviderRegistry | None = None,
) -> ClassificationResult:
    """Convenience entry point using the checked-in registry by default."""
    return (registry or default_registry()).classify(signal)
