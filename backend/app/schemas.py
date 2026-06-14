"""Pydantic v2 schemas matching docs/API_CONTRACT.md field-for-field."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import ScanStatus, Severity, SourceType, Tool, TriageStatus


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total: int = 0


class ScanCreateGit(BaseModel):
    """Body for `POST /api/scans` when submitting a git URL."""

    source_type: str
    source_ref: str


class ScanCreateResponse(BaseModel):
    """`201` response for `POST /api/scans`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: SourceType
    source_ref: str
    status: ScanStatus
    created_at: datetime


class ScanListItem(BaseModel):
    """An item of `GET /api/scans`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: SourceType
    source_ref: str
    status: ScanStatus
    created_at: datetime
    finished_at: datetime | None = None
    counts: SeverityCounts


class ScanDetail(ScanListItem):
    """`GET /api/scans/{id}` — list item shape + started_at + error."""

    started_at: datetime | None = None
    error: str | None = None


class FindingOut(BaseModel):
    """An item of `GET /api/scans/{id}/findings` (raw excluded)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tool: Tool
    rule_id: str
    severity: Severity
    title: str
    message: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    cwe: str | None = None
    owasp: str | None = None
    triage_status: TriageStatus = TriageStatus.open
    triage_note: str | None = None
    triaged_at: datetime | None = None


class TriageUpdate(BaseModel):
    """Body for `PATCH /api/scans/{id}/findings/{finding_id}`."""

    triage_status: TriageStatus
    triage_note: str | None = None


class RawFinding(BaseModel):
    """Normalized-but-not-yet-persisted finding produced by a scanner runner."""

    tool: Tool
    rule_id: str
    severity: Severity
    title: str
    message: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    cwe: str | None = None
    owasp: str | None = None
    raw: dict[str, Any]
