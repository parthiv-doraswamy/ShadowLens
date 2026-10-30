"""SQLite persistence foundation for privacy-safe ShadowLens records."""
from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import Engine
from sqlalchemy import event as sqlalchemy_event
from sqlmodel import Field, Session, SQLModel, create_engine, select

from app.models.contracts import AITool, Event, Finding


class AssetRow(SQLModel, table=True):
    __tablename__ = "assets"
    host_id: str = Field(primary_key=True)
    hostname_hash: str | None = None
    os: str | None = None
    first_seen: str
    last_seen: str


class AIToolRow(SQLModel, table=True):
    __tablename__ = "ai_tools"
    tool_id: str = Field(primary_key=True)
    host_id: str = Field(foreign_key="assets.host_id", index=True)
    name: str
    kind: str
    provider: str | None = None
    sanctioned: bool | None = None
    discovery: str
    first_seen: str
    last_seen: str
    capabilities_json: str = "[]"


class EventRow(SQLModel, table=True):
    __tablename__ = "events"
    event_id: str = Field(primary_key=True)
    ts: str = Field(index=True)
    host_id: str = Field(foreign_key="assets.host_id", index=True)
    tool_id: str | None = Field(default=None, foreign_key="ai_tools.tool_id")
    source: str
    tier: str
    provider: str | None = None
    dst_host: str | None = None
    dst_port: int | None = None
    bytes_out: int | None = None
    bytes_in: int | None = None
    process_name: str | None = None
    meta_json: str


class FindingRow(SQLModel, table=True):
    __tablename__ = "findings"
    finding_id: str = Field(primary_key=True)
    ts: str
    host_id: str | None = Field(default=None, foreign_key="assets.host_id", index=True)
    tool_id: str | None = Field(default=None, foreign_key="ai_tools.tool_id")
    category: str
    rule_id: str
    severity: str = Field(index=True)
    confidence: float
    tier: str
    evidence_json: str
    controls_json: str
    status: str = Field(default="open", index=True)
    triage_json: str | None = None


class FindingEventRow(SQLModel, table=True):
    __tablename__ = "finding_events"
    finding_id: str = Field(foreign_key="findings.finding_id", primary_key=True)
    event_id: str = Field(foreign_key="events.event_id", primary_key=True)


class SecretVaultRow(SQLModel, table=True):
    __tablename__ = "secret_vault"
    hmac: str = Field(primary_key=True)
    kind: str
    first_seen: str
    seen_count: int = Field(default=1, ge=1)


class CanaryRow(SQLModel, table=True):
    __tablename__ = "canaries"
    canary_id: str = Field(primary_key=True)
    kind: str
    hmac: str
    planted_path: str
    created: str
    triggered_at: str | None = None


class RiskSnapshotRow(SQLModel, table=True):
    __tablename__ = "risk_snapshots"
    id: int | None = Field(default=None, primary_key=True)
    ts: str = Field(index=True)
    scope: str
    scope_id: str
    score: float
    breakdown_json: str


class PolicyRow(SQLModel, table=True):
    __tablename__ = "policies"
    policy_id: str = Field(primary_key=True)
    yaml: str
    active: bool = Field(default=False)


class SchemaMigrationRow(SQLModel, table=True):
    __tablename__ = "schema_migrations"
    version: int = Field(primary_key=True)
    applied_at: str


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create a SQLite engine with WAL, foreign keys and bounded busy wait."""
    default_path = Path(os.getenv("SHADOWLENS_DB_PATH", ".shadowlens/shadowlens.db"))
    default_url = f"sqlite:///{default_path.as_posix()}"
    url = database_url
    if url is None:
        url = os.getenv("SHADOWLENS_DATABASE_URL")
    if url is None:
        url = default_url
    engine = create_engine(
        url, connect_args={"check_same_thread": False, "timeout": 5.0}, echo=False
    )

    @sqlalchemy_event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def initialize_database(engine: Engine) -> None:
    """Apply the initial additive schema migration; safe to call repeatedly."""
    database_path: Path | None = None
    database_name = engine.url.database
    if (
        engine.dialect.name == "sqlite"
        and database_name is not None
        and database_name not in {"", ":memory:"}
    ):
        database_path = Path(database_name).expanduser()
        parent_existed = database_path.parent.exists()
        database_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt" and not parent_existed:
            database_path.parent.chmod(0o700)
        if database_path.is_symlink():
            raise ValueError("SQLite database path must not be a symbolic link")

    previous_umask = os.umask(0o077) if os.name != "nt" else None
    try:
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            if session.get(SchemaMigrationRow, 1) is None:
                session.add(SchemaMigrationRow(version=1, applied_at=_utc_now()))
                session.commit()
    finally:
        if previous_umask is not None:
            os.umask(previous_umask)

    if database_path is not None and os.name != "nt" and database_path.exists():
        database_path.chmod(0o600)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Yield a session and guarantee commit or rollback for one transaction."""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def _ensure_asset(session: Session, host_id: str, ts: str) -> None:
    asset = session.get(AssetRow, host_id)
    if asset is None:
        session.add(AssetRow(host_id=host_id, first_seen=ts, last_seen=ts))
    else:
        asset.first_seen = min(asset.first_seen, ts)
        asset.last_seen = max(asset.last_seen, ts)


def save_event(session: Session, event: Event) -> None:
    """Persist canonical metadata only; never persist transient body handles."""
    payload = event.model_dump(mode="json")
    http = payload.get("http")
    if isinstance(http, dict):
        http.pop("body_ref", None)
    ts = event.ts.isoformat()
    _ensure_asset(session, event.host_id, ts)
    session.add(EventRow(
        event_id=str(event.event_id), ts=ts, host_id=event.host_id,
        source=event.source.value, tier=event.tier.value,
        provider=event.ai.provider if event.ai else None,
        dst_host=event.net.dst_host if event.net else None,
        dst_port=event.net.dst_port if event.net else None,
        bytes_out=event.net.bytes_out if event.net else None,
        bytes_in=event.net.bytes_in if event.net else None,
        process_name=event.process.name if event.process else None,
        meta_json=json.dumps(payload, separators=(",", ":"), sort_keys=True),
    ))


def save_finding(session: Session, finding: Finding, host_id: str | None = None) -> None:
    """Persist masked evidence and event links in the caller's transaction."""
    for event_id in finding.event_ids:
        if session.get(EventRow, str(event_id)) is None:
            raise ValueError(f"finding references unknown event: {event_id}")
    ts = finding.created_at.isoformat()
    if host_id is not None:
        _ensure_asset(session, host_id, ts)
    payload = finding.model_dump(mode="json")
    session.add(FindingRow(
        finding_id=str(finding.finding_id), ts=ts, host_id=host_id,
        category=finding.category.value, rule_id=finding.rule_id,
        severity=finding.severity.value, confidence=finding.confidence,
        tier=finding.tier.value,
        evidence_json=json.dumps(payload["evidence"], separators=(",", ":"), sort_keys=True),
        controls_json=json.dumps(finding.mapped_controls, separators=(",", ":")),
        status=finding.status.value,
        triage_json=(
            json.dumps(payload["triage"], separators=(",", ":"), sort_keys=True)
            if payload.get("triage") is not None else None
        ),
    ))
    session.flush()
    session.add_all([
        FindingEventRow(finding_id=str(finding.finding_id), event_id=str(event_id))
        for event_id in finding.event_ids
    ])


def save_ai_tool(session: Session, tool: AITool) -> None:
    """Persist a discovered tool and maintain its host asset."""
    first_seen = tool.first_seen.isoformat()
    last_seen = tool.last_seen.isoformat()
    _ensure_asset(session, tool.host_id, first_seen)
    row = session.get(AIToolRow, str(tool.tool_id))
    capabilities_json = json.dumps(tool.capabilities, separators=(",", ":"))
    if row is None:
        session.add(AIToolRow(
            tool_id=str(tool.tool_id),
            host_id=tool.host_id,
            name=tool.name,
            kind=tool.kind.value,
            provider=tool.provider,
            sanctioned=tool.sanctioned,
            discovery=tool.discovery.value,
            first_seen=first_seen,
            last_seen=last_seen,
            capabilities_json=capabilities_json,
        ))
    else:
        row.host_id = tool.host_id
        row.name = tool.name
        row.kind = tool.kind.value
        row.provider = tool.provider
        row.sanctioned = tool.sanctioned
        row.discovery = tool.discovery.value
        row.first_seen = first_seen
        row.last_seen = last_seen
        row.capabilities_json = capabilities_json


def get_event(session: Session, event_id: UUID) -> EventRow | None:
    return session.exec(select(EventRow).where(EventRow.event_id == str(event_id))).first()
