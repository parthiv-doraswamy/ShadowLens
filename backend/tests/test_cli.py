from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from sqlmodel import Session

from app.cli import CLIError, initialize_local_state, run_server
from app.config import Settings
from app.persistence import SchemaMigrationRow, create_database_engine


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        data_dir=tmp_path / ".shadowlens",
        token_file=None,
        database_url=f"sqlite:///{tmp_path / '.shadowlens' / 'shadowlens.db'}",
        api_token=None,
        cors_origins="",
    )


def test_init_creates_private_local_state_and_is_idempotent(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)

    first = initialize_local_state(settings)

    data_dir = tmp_path / ".shadowlens"
    token_file = data_dir / "access.token"
    database_file = data_dir / "shadowlens.db"
    policy_file = data_dir / "policy.default.yaml"
    assert first["policy_created"] is True
    assert token_file.is_file()
    assert database_file.is_file()
    assert policy_file.is_file()
    assert "non-enforcing" in policy_file.read_text(encoding="utf-8")
    assert token_file.read_text(encoding="utf-8").strip()
    assert len(token_file.read_text(encoding="utf-8").strip()) >= 32

    if os.name != "nt":
        assert stat.S_IMODE(data_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE(token_file.stat().st_mode) == 0o600
        assert stat.S_IMODE(database_file.stat().st_mode) == 0o600
        assert stat.S_IMODE(policy_file.stat().st_mode) == 0o600

    policy_file.write_text("# operator-owned policy\n", encoding="utf-8")
    second = initialize_local_state(settings)
    assert second["policy_created"] is False
    assert policy_file.read_text(encoding="utf-8") == "# operator-owned policy\n"

    engine = create_database_engine(settings.resolved_database_url)
    try:
        with Session(engine) as session:
            assert session.get(SchemaMigrationRow, 1) is not None
    finally:
        engine.dispose()


def test_init_preserves_existing_data_directory_permissions(tmp_path: Path) -> None:
    data_dir = tmp_path / "shared"
    data_dir.mkdir()
    if os.name != "nt":
        data_dir.chmod(0o755)
    settings = Settings(
        _env_file=None,
        data_dir=data_dir,
        database_url=f"sqlite:///{data_dir / 'shadowlens.db'}",
        cors_origins="",
    )

    initialize_local_state(settings)

    if os.name != "nt":
        assert stat.S_IMODE(data_dir.stat().st_mode) == 0o755


def test_serve_uses_loopback_and_disables_uvicorn_access_log(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.cli as cli

    captured: dict[str, object] = {}

    def fake_run(app_path: str, **kwargs: object) -> None:
        captured["app_path"] = app_path
        captured.update(kwargs)

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)
    settings = Settings(_env_file=None, cors_origins="")

    run_server(settings, port_override=8123)

    assert captured["app_path"] == "app.main:app"
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8123
    assert captured["access_log"] is False


def test_serve_rejects_non_loopback_and_unimplemented_adapters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.cli as cli

    called = False

    def fake_run(_app_path: str, **_kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)
    settings = Settings(_env_file=None, cors_origins="")

    with pytest.raises(ValueError):
        run_server(settings, host_override="0.0.0.0")
    with pytest.raises(CLIError, match="live capture is not implemented"):
        run_server(settings, live=True)
    with pytest.raises(CLIError, match="Lens Gateway is not implemented"):
        run_server(settings, gateway=True)
    assert called is False
