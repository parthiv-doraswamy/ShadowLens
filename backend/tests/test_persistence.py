from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.contracts import Event, Finding
from app.persistence import (
    FindingEventRow,
    FindingRow,
    SchemaMigrationRow,
    create_database_engine,
    get_event,
    initialize_database,
    save_event,
    save_finding,
)


def make_event(**overrides: object) -> Event:
    payload: dict[str, object] = {
        "event_id": str(uuid4()),
        "ts": datetime(2026, 10, 30, 10, 0, tzinfo=UTC).isoformat(),
        "source": "socket", "tier": "T1", "host_id": "host-fingerprint",
        "process": {"pid": 123, "name": "editor"},
        "net": {"dst_host": "api.openai.com", "dst_port": 443, "bytes_out": 10},
        "http": {
            "method": "POST", "path": "/v1/chat/completions",
            "headers": {"authorization": "Bearer never-persist-this"},
            "body_ref": "transient-buffer-never-persist-this",
        },
        "ai": {"provider": "openai", "kind": "cloud"},
        "raw_visibility": "metadata",
    }
    payload.update(overrides)
    return Event.model_validate(payload)


def make_finding(event_id: str) -> Finding:
    return Finding.model_validate({
        "event_ids": [event_id], "category": "secret",
        "rule_id": "SEC-AWS-ACCESS-KEY", "severity": "high",
        "confidence": 0.9, "tier": "T3",
        "evidence": {
            "masked": "AKIA************MPLE", "hmac": "hmac-sha256:test",
            "offset": 12, "context_redacted": "key=AKIA****",
        },
    })


@pytest.fixture
def engine(tmp_path):
    database = tmp_path / "nested" / "shadowlens.db"
    db_engine = create_database_engine(f"sqlite:///{database}")
    initialize_database(db_engine)
    yield db_engine
    db_engine.dispose()


def test_initial_migration_is_idempotent_and_wal_enabled(engine) -> None:
    initialize_database(engine)
    with Session(engine) as session:
        assert session.get(SchemaMigrationRow, 1) is not None
        assert len(session.exec(select(SchemaMigrationRow)).all()) == 1
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_event_persistence_excludes_transient_secrets(engine) -> None:
    event = make_event()
    with Session(engine) as session:
        save_event(session, event)
        session.commit()
        row = get_event(session, event.event_id)
        assert row is not None
        assert row.provider == "openai"
        assert "body_ref" not in row.meta_json
        assert "transient-buffer-never-persist-this" not in row.meta_json
        assert "never-persist-this" not in row.meta_json
    indexes = {index["name"] for index in inspect(engine).get_indexes("events")}
    assert "ix_events_ts" in indexes


def test_finding_and_event_link_are_persisted_atomically(engine) -> None:
    event = make_event()
    finding = make_finding(str(event.event_id))
    with Session(engine) as session:
        save_event(session, event)
        save_finding(session, finding, host_id=event.host_id)
        session.commit()
    with Session(engine) as session:
        stored = session.get(FindingRow, str(finding.finding_id))
        links = session.exec(select(FindingEventRow)).all()
        assert stored is not None
        assert stored.severity == "high"
        assert len(links) == 1
        assert links[0].event_id == str(event.event_id)


def test_finding_rejects_unknown_event_reference(engine) -> None:
    finding = make_finding(str(uuid4()))
    with Session(engine) as session:
        with pytest.raises(ValueError, match="unknown event"):
            save_finding(session, finding)
        session.rollback()
        assert session.exec(select(FindingRow)).first() is None


def test_foreign_key_and_transaction_rollback(engine) -> None:
    event = make_event()
    with Session(engine) as session:
        save_event(session, event)
        session.commit()
    with Session(engine) as session:
        session.add(FindingEventRow(finding_id=str(uuid4()), event_id=str(event.event_id)))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.exec(select(FindingEventRow)).first() is None


def test_schema_contains_required_core_tables(engine) -> None:
    table_names = set(inspect(engine).get_table_names())
    assert {
        "assets", "ai_tools", "events", "findings", "finding_events",
        "secret_vault", "canaries", "risk_snapshots", "policies",
    }.issubset(table_names)
    finding_indexes = {index["name"] for index in inspect(engine).get_indexes("findings")}
    assert "ix_findings_severity" in finding_indexes
    assert "ix_findings_status" in finding_indexes
