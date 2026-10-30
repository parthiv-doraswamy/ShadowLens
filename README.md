# ShadowLens

Local-first AI Shadow IT, sensitive-data exposure, and agent-governance auditing platform.

> **Status:** Specification extraction and architecture documentation complete. Product implementation has not yet started beyond the initial FastAPI/React bootstrap.

## Source of truth

- `ShadowLens_Unified_Master_Specification.md` — authoritative product specification.
- `docs/requirements/requirements_catalog.md` — 50 functional/privacy requirement IDs, 15 novelty features, 10 NFRs, APIs, rules, providers and scenarios.
- `docs/requirements/acceptance_criteria.md` — source-derived acceptance criteria.
- `docs/requirements/implementation_backlog.md` — milestone M0–M8 backlog and phase gates.
- `docs/requirements/human_approval_gates.md` — explicit permission and opt-in boundaries.
- `docs/requirements/traceability_matrix.md` — requirement-to-module/chunk/test/outcome mapping.
- `docs/architecture/` — system, backend, frontend, event pipeline, data model, privacy boundary and threat model.

## Technology baseline

- Python 3.11+ · FastAPI · asyncio · Pydantic v2 · SQLModel · SQLite WAL
- psutil · dpkt · optional Scapy · optional httpx gateway
- React · TypeScript · Vite · Tailwind CSS · shadcn/ui
- pytest · Hypothesis · Playwright · Ruff · mypy

## Local development

Prerequisites: Python 3.11+ and a current Node.js LTS release with npm.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Current bootstrap health endpoint: http://127.0.0.1:8000/api/v1/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Architecture and privacy principles

- Modular monolith; replaceable collectors emit one canonical event.
- Deterministic detection and explainable risk precede optional advisory LLM triage.
- T1 observed metadata, T2 inferred flow shape and T3 authorized plaintext remain distinct.
- DERIVED and UNAVAILABLE are separate evidence states.
- No TLS interception or claim of passive HTTPS body inspection.
- Raw payloads are transient; secrets/prompts are not persisted by default.
- Local-only and loopback defaults; optional integrations require explicit opt-in.
- Core product must work without LLM credentials.

## Current implementation status

Repository/bootstrap CI is in place. The current backend is a minimal FastAPI health endpoint and the frontend is a bootstrap screen. Canonical models, SQLite repositories, event queue, collectors, detection engines, API routes and dashboard workflows remain future implementation work.

## Validation

GitHub Actions currently runs backend install/Ruff/pytest and frontend install/typecheck/build. A passing bootstrap workflow does not imply product requirements are implemented.
