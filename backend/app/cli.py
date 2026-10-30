"""Local-first ShadowLens command-line entry point."""
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

import uvicorn
from pydantic import ValidationError

from app.config import Settings, validate_loopback_host
from app.persistence import create_database_engine, initialize_database
from app.security import load_or_create_api_token

DEFAULT_POLICY_STARTER = """# ShadowLens default policy starter.
# This file is intentionally non-enforcing in this release.
# No rules are enabled until the versioned policy contract and evaluator are implemented.
"""


class CLIError(RuntimeError):
    """Safe, operator-readable CLI failure."""


def _ensure_private_directory(path: Path) -> None:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise CLIError("data directory must not be a symbolic link")
    existed = expanded.exists()
    expanded.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not expanded.is_dir():
        raise CLIError("data directory path is not a directory")
    if os.name != "nt" and not existed:
        expanded.chmod(0o700)


def _write_policy_starter(path: Path) -> bool:
    if path.is_symlink():
        raise CLIError("policy starter path must not be a symbolic link")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        if not path.is_file():
            raise CLIError("policy starter path exists and is not a regular file")
        return False
    with os.fdopen(descriptor, "w", encoding="utf-8") as policy_file:
        policy_file.write(DEFAULT_POLICY_STARTER)
        policy_file.flush()
        os.fsync(policy_file.fileno())
    return True


def initialize_local_state(settings: Settings) -> dict[str, str | bool]:
    """Create private local state, first-run token, SQLite schema and inert policy starter."""
    _ensure_private_directory(settings.data_dir)
    token_path = settings.resolved_token_file
    api_token = settings.api_token.get_secret_value() if settings.api_token else None
    load_or_create_api_token(token_path, configured_token=api_token)

    engine = create_database_engine(settings.resolved_database_url)
    try:
        initialize_database(engine)
    finally:
        engine.dispose()

    policy_path = settings.data_dir.expanduser() / "policy.default.yaml"
    policy_created = _write_policy_starter(policy_path)
    return {
        "data_dir": str(settings.data_dir.expanduser()),
        "database_url": settings.resolved_database_url,
        "token_file": "" if api_token is not None else str(token_path),
        "policy_file": str(policy_path),
        "policy_created": policy_created,
        "operator_token_configured": api_token is not None,
    }


def run_server(
    settings: Settings,
    *,
    host_override: str | None = None,
    port_override: int | None = None,
    reload: bool = False,
    live: bool = False,
    gateway: bool = False,
) -> None:
    """Start the API on loopback; unsupported privileged adapters fail closed."""
    if live:
        raise CLIError("live capture is not implemented; no packet capture was started")
    if gateway:
        raise CLIError("Lens Gateway is not implemented; no proxy was started")
    host = validate_loopback_host(host_override or settings.host)
    port = port_override if port_override is not None else settings.port
    if port < 1 or port > 65535:
        raise CLIError("port must be between 1 and 65535")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        access_log=False,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shadowlens",
        description="Local-first AI Shadow IT and agent-governance auditing.",
    )
    commands = parser.add_subparsers(dest="command")

    init_parser = commands.add_parser(
        "init",
        help="create the local data directory, API token, SQLite database and policy starter",
    )
    init_parser.set_defaults(action="init")

    serve_parser = commands.add_parser(
        "serve",
        help="start the local ShadowLens API (loopback only)",
    )
    serve_parser.add_argument("--host", help="loopback bind address (default: SHADOWLENS_HOST)")
    serve_parser.add_argument("--port", type=int, help="listen port (default: SHADOWLENS_PORT)")
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="enable Uvicorn development reload",
    )
    serve_parser.add_argument(
        "--live",
        action="store_true",
        help="request live capture (not yet available)",
    )
    serve_parser.add_argument(
        "--gateway",
        action="store_true",
        help="request Lens Gateway (not yet available)",
    )
    serve_parser.set_defaults(action="serve")
    return parser


def _safe_settings_error(exc: ValidationError) -> str:
    messages = [
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors(include_input=False)
    ]
    return "; ".join(messages)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the supported CLI command and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    try:
        settings = Settings()
        if args.action == "init":
            result = initialize_local_state(settings)
            print(f"ShadowLens local state initialized: {result['data_dir']}")
            print(f"Database: {result['database_url']}")
            if result["operator_token_configured"]:
                print("Authentication uses the configured SHADOWLENS_API_TOKEN; its value is not displayed.")
            else:
                print(f"API token file: {result['token_file']}")
                print("A new random API token was created; read it from the owner-only token file.")
            print(f"Policy starter: {result['policy_file']}")
            if not result["policy_created"]:
                print("Existing policy starter preserved.")
            return 0

        run_server(
            settings,
            host_override=args.host,
            port_override=args.port,
            reload=args.reload,
            live=args.live,
            gateway=args.gateway,
        )
        return 0
    except ValidationError as exc:
        print(f"Invalid ShadowLens settings: {_safe_settings_error(exc)}", file=sys.stderr)
        return 2
    except (CLIError, OSError, ValueError) as exc:
        print(f"ShadowLens: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
