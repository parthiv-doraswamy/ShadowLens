# ShadowLens backend

Local FastAPI application and CLI.

## Install and run

From this directory with Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
shadowlens init
shadowlens serve
```

The API binds to 127.0.0.1:8000 by default. Use shadowlens --help and shadowlens serve --help for supported options.

## CLI scope

- shadowlens init creates the local data directory, first-run bearer token, SQLite schema and a non-enforcing policy starter.
- shadowlens serve starts the API using loopback only by default.
- serve --live and serve --gateway are intentionally unavailable until their adapters meet the specification's permission and privacy gates.

## Settings

Settings are read from SHADOWLENS_* environment variables and an optional .env in the current working directory. Non-loopback bind addresses and non-loopback CORS origins are rejected.
