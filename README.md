# ShadowLens

Local-first AI Shadow IT, sensitive-data exposure, and agent-governance auditing platform.

> **Status:** Repository bootstrap. Product implementation has not started.
>
> The source-of-truth specification `ShadowLens_Unified_Master_Specification.md` must be added to the repository root before requirement extraction and product implementation.

## Technology baseline

- Python 3.11+ · FastAPI · asyncio · Pydantic v2 · SQLModel · SQLite WAL
- React · TypeScript · Vite · Tailwind CSS
- pytest · Ruff · mypy · Playwright

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

Health endpoint: http://127.0.0.1:8000/api/v1/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Specification prerequisite

Add `ShadowLens_Unified_Master_Specification.md` to the repository root. All requirement IDs and acceptance criteria will be derived from it, not guessed.

## License

Not yet selected.
