"""Validated local-first ShadowLens runtime settings."""
from __future__ import annotations

import ipaddress
import math
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def validate_loopback_host(value: str) -> str:
    """Accept only localhost or a literal loopback IP address."""
    host = value.strip().lower()
    if host == "localhost":
        return host
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("host must be localhost or a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("ShadowLens must bind to a loopback address")
    return host


def _validate_local_origin(origin: str) -> str:
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("CORS origins must be local HTTP(S) origins without paths or credentials")
    validate_loopback_host(parsed.hostname)
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("CORS origin has an invalid port") from exc
    return origin.rstrip("/")


class Settings(BaseSettings):
    """Environment-backed settings with safe local-only defaults."""

    model_config = SettingsConfigDict(
        env_prefix="SHADOWLENS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = "development"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    data_dir: Path = Path(".shadowlens")
    token_file: Path | None = None
    database_url: str | None = None
    db_path: Path | None = None
    api_token: SecretStr | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    event_queue_capacity: int = Field(default=256, ge=1, le=100_000)
    event_workers: int = Field(default=1, ge=1, le=32)
    ingest_timeout_seconds: float = Field(default=1.0, gt=0, le=60)
    log_level: str = "INFO"

    @field_validator("host")
    @classmethod
    def loopback_only_host(cls, value: str) -> str:
        return validate_loopback_host(value)

    @field_validator("database_url")
    @classmethod
    def sqlite_only_database(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("sqlite:///"):
            raise ValueError("only local SQLite database URLs are supported")
        return value

    @field_validator("api_token", mode="before")
    @classmethod
    def blank_token_is_unset(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("api_token")
    @classmethod
    def require_strong_token(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and len(value.get_secret_value()) < 32:
            raise ValueError("SHADOWLENS_API_TOKEN must contain at least 32 characters")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_allowlist(cls, value: str) -> str:
        origins = [item.strip() for item in value.split(",") if item.strip()]
        for origin in origins:
            _validate_local_origin(origin)
        return ",".join(origins)

    @field_validator("log_level")
    @classmethod
    def valid_log_level(cls, value: str) -> str:
        level = value.strip().upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("SHADOWLENS_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR or CRITICAL")
        return level

    @field_validator("ingest_timeout_seconds")
    @classmethod
    def finite_timeout(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("SHADOWLENS_INGEST_TIMEOUT_SECONDS must be finite")
        return value

    @property
    def resolved_token_file(self) -> Path:
        return (self.token_file or self.data_dir / "access.token").expanduser()

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_path:
            path = self.db_path.expanduser()
        else:
            path = self.data_dir.expanduser() / "shadowlens.db"
        return f"sqlite:///{path.as_posix()}"

    @property
    def cors_allow_origins(self) -> list[str]:
        return [origin for origin in self.cors_origins.split(",") if origin]
