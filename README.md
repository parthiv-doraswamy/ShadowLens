# ShadowLens

Local-first AI Shadow IT, sensitive-data exposure, and agent-governance auditing platform.

> **Implementation status:** Bootstrap, canonical contracts, SQLite persistence, bounded event pipeline, authenticated metadata ingestion, structured logging, local CLI initialization, provider registry (REQ-DISC-001) and metadata-only HAR/JSON/JSONL import (REQ-COL-003) are implemented incrementally. Live process/socket and PCAP collectors, content inspection/detection, and dashboard-to-API integration remain in progress.

## Source of truth

- `ShadowLens_Unified_Master_Specification.md` — authoritative product specification.
- `docs/requirements/requirements_catalog.md` — functional/privacy requirements, novelty features and NFRs.
- `docs/requirements/acceptance_criteria.md` — source-derived acceptance criteria.
- `docs/requirements/implementation_backlog.md` — milestone backlog and phase gates.
- `docs/requirements/human_approval_gates.md` — explicit permission and opt-in boundaries.
- `docs/requirements/traceability_matrix.md` — requirement-to-module/chunk/test/outcome mapping.
- `docs/architecture/` — system, backend, frontend, event pipeline, data model, privacy and threat-model documents.

## Technology baseline

- Python 3.11+ · FastAPI · asyncio · Pydantic v2 · SQLModel · SQLite WAL
- structlog JSON logs · psutil · dpkt · optional Scapy · optional httpx gateway
- React · TypeScript · Vite · Tailwind CSS
- pytest · Playwright · Ruff · mypy

## Local backend quick start

Prerequisites: Python 3.11+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
shadowlens init
shadowlens serve
```

The API binds to `127.0.0.1:8000` by default. Its unauthenticated health check is [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health). Operational API routes require the bearer token stored in the owner-only `.shadowlens/access.token` file. Do not paste the token into logs, tickets or source control.

The CLI supports `init`, `serve` and `ingest <file>`. The importer accepts HAR, mitmproxy JSON, nginx/squid-style JSONL and ShadowLens normalized mock-log JSON. It emits T1 metadata only, redacts sensitive headers and discards request/response bodies. The initial upload cap is 25 MiB and the record cap is 10,000. Bodies are not yet routed to a detector/inspector. `serve --live` and `serve --gateway` fail closed because those adapters are not implemented yet. The initial policy file is an inert starter; there is no active policy evaluator yet.

### Configuration

Copy `.env.example` to `.env` in the directory from which you run ShadowLens, then adjust local settings as required. Settings use the `SHADOWLENS_` prefix. The host and CORS origin validators reject non-loopback values. SQLite, the random local token and structured JSON logs are the defaults.

### Frontend development

```bash
cd frontend
npm install
npm run dev
```

The frontend currently contains design-system, landing-page and synthetic dashboard templates; the pages are not yet connected to live backend services.

## Architecture and privacy principles

- Modular monolith; replaceable collectors emit one canonical event.
- Deterministic detection and explainable risk precede optional advisory LLM triage.
- T1 observed metadata, T2 inferred flow shape and T3 authorized plaintext remain distinct.
- DERIVED and UNAVAILABLE are separate evidence states.
- No TLS interception or claim of passive HTTPS body inspection.
- Raw payloads are transient; secrets/prompts are not persisted by default.
- Local-only and loopback defaults; optional integrations require explicit opt-in.
- Core product must work without LLM credentials.

## Validation

GitHub Actions runs backend Ruff/mypy/pytest, frontend typecheck/build/Playwright, Gitleaks, Semgrep and CodeQL. A passing bootstrap or foundation workflow does not imply every product requirement is implemented. See per-chunk reports in `docs/reports/`.
