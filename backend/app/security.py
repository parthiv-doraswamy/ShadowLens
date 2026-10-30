"""Local bearer-token creation and loading for the ShadowLens API."""
from __future__ import annotations

import os
import secrets
from pathlib import Path


def _default_token_path() -> Path:
    configured_path = os.getenv("SHADOWLENS_TOKEN_FILE")
    if configured_path:
        return Path(configured_path).expanduser()
    data_dir = Path(os.getenv("SHADOWLENS_DATA_DIR", ".shadowlens")).expanduser()
    return data_dir / "access.token"


def load_or_create_api_token(token_path: Path | None = None) -> str:
    """Load an operator token or create a random, owner-only token on first run.

    SHADOWLENS_API_TOKEN is an explicit deployment override. Otherwise the token
    is stored in a 0600 file under the local ShadowLens data directory.
    """
    configured_token = os.getenv("SHADOWLENS_API_TOKEN")
    if configured_token:
        if len(configured_token) < 32:
            raise ValueError("SHADOWLENS_API_TOKEN must contain at least 32 characters")
        return configured_token

    path = token_path or _default_token_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        path.parent.chmod(0o700)

    if path.is_symlink():
        raise ValueError("API token path must not be a symbolic link")

    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        if path.is_symlink() or not path.is_file():
            raise ValueError("API token path must be a regular file") from None
        if os.name != "nt":
            path.chmod(0o600)
        read_flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            read_flags |= os.O_NOFOLLOW
        descriptor = os.open(path, read_flags)
        with os.fdopen(descriptor, "r", encoding="utf-8") as token_file:
            token = token_file.read(513).strip()
        if len(token) < 32 or len(token) > 512:
            raise ValueError("stored API token is empty or has an invalid length") from None
        return token

    token = secrets.token_urlsafe(32)
    with os.fdopen(descriptor, "w", encoding="utf-8") as token_file:
        token_file.write(token + "\n")
        token_file.flush()
        os.fsync(token_file.fileno())
    return token
