"""Minimal FastAPI application for the repository bootstrap."""

from fastapi import FastAPI

app = FastAPI(
    title="ShadowLens API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/api/v1/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return a process-level health response."""
    return {"status": "ok"}
