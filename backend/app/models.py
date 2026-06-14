"""SQLAlchemy ORM models — scans and findings (docs/DATA_MODEL.md)."""

from __future__ import annotations

import enum
import hashlib
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SourceType(str, enum.Enum):
    zip = "zip"
    git = "git"


class ScanStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Tool(str, enum.Enum):
    gitleaks = "gitleaks"
    semgrep = "semgrep"
    trivy = "trivy"


class Severity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class TriageStatus(str, enum.Enum):
    open = "open"
    false_positive = "false_positive"
    resolved = "resolved"
    suppressed = "suppressed"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type"), nullable=False
    )
    source_ref: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus, name="scan_status"),
        nullable=False,
        default=ScanStatus.queued,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SHA-256 over the materialized file tree — lets an identical re-submission
    # reuse a prior completed scan's findings instead of re-running scanners.
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    findings: Mapped[list["Finding"]] = relationship(
        back_populates="scan",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool: Mapped[Tool] = mapped_column(Enum(Tool, name="tool"), nullable=False)
    rule_id: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cwe: Mapped[str | None] = mapped_column(Text, nullable=True)
    owasp: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw: Mapped[dict] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False)

    # Stable identity of a finding across scans: md5(tool:rule_id:file_path:line_start).
    # Powers triage carry-over and the "new since last scan" baseline filter.
    fingerprint: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    triage_status: Mapped[TriageStatus] = mapped_column(
        Enum(TriageStatus, name="triage_status"),
        nullable=False,
        default=TriageStatus.open,
        server_default=TriageStatus.open.value,
    )
    triage_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="findings")


def finding_fingerprint(tool, rule_id: str, file_path: str, line_start: int | None) -> str:
    """Stable cross-scan identity: md5(tool:rule_id:file_path:line_start).

    Must stay in lockstep with the SQL backfill in migration 0003.
    """
    tool_val = tool.value if isinstance(tool, Tool) else str(tool)
    line = "" if line_start is None else str(line_start)
    basis = f"{tool_val}:{rule_id}:{file_path}:{line}"
    return hashlib.md5(basis.encode("utf-8")).hexdigest()
