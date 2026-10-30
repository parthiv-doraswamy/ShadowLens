from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import create_app
from app.persistence import SchemaMigrationRow


def test_health_reports_database_bus_and_unconfigured_collectors(tmp_path: Path) -> None:
    database_path = tmp_path / "health.db"
    app = create_app(
        database_url=f"sqlite:///{database_path}",
        token_path=tmp_path / "access.token",
    )

    with TestClient(app) as client:
        response = client.get("/api/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["database"]["status"] == "ok"
        assert payload["event_bus"]["status"] == "accepting"
        assert payload["event_bus"]["workers"] == 1
        assert payload["collectors"]["status"] == "not_configured"
        with Session(app.state.database_engine) as session:
            assert session.get(SchemaMigrationRow, 1) is not None
