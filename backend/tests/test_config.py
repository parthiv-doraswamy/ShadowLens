from __future__ import annotations

from pydantic import ValidationError

import pytest

from app.config import Settings


def test_settings_default_to_loopback_and_local_cors() -> None:
    settings = Settings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.cors_allow_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    assert settings.event_queue_capacity == 256
    assert settings.event_workers == 1
    assert settings.resolved_token_file == settings.data_dir / "access.token"
    assert settings.resolved_database_url.startswith("sqlite:///")


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.20", "example.com"])
def test_settings_reject_non_loopback_bind_addresses(host: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, host=host)


@pytest.mark.parametrize(
    "origin",
    [
        "https://example.com",
        "http://192.168.1.20:5173",
        "*",
        "http://localhost:5173/path",
        "http://user@localhost:5173",
    ],
)
def test_settings_reject_non_local_or_malformed_cors_origins(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins=origin)


def test_settings_accept_loopback_ipv6_and_blank_api_token() -> None:
    settings = Settings(
        _env_file=None,
        host="::1",
        cors_origins="http://[::1]:5173",
        api_token="",
    )

    assert settings.host == "::1"
    assert settings.cors_allow_origins == ["http://[::1]:5173"]
    assert settings.api_token is None


def test_settings_reject_unsupported_database_and_weak_token() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql://localhost/shadowlens")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, api_token="too-short")
