"""initial schema: scans + findings

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create_type=False: we create the enum types explicitly below, so
    # create_table must not try to (re)create them via its own DDL events.
    source_type = postgresql.ENUM("zip", "git", name="source_type", create_type=False)
    scan_status = postgresql.ENUM(
        "queued", "running", "completed", "failed", name="scan_status", create_type=False
    )
    tool = postgresql.ENUM("gitleaks", "semgrep", "trivy", name="tool", create_type=False)
    severity = postgresql.ENUM(
        "critical", "high", "medium", "low", "info", name="severity", create_type=False
    )

    source_type.create(op.get_bind(), checkfirst=True)
    scan_status.create(op.get_bind(), checkfirst=True)
    tool.create(op.get_bind(), checkfirst=True)
    severity.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=False),
        sa.Column("status", scan_status, nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool", tool, nullable=False),
        sa.Column("rule_id", sa.Text(), nullable=False),
        sa.Column("severity", severity, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("cwe", sa.Text(), nullable=True),
        sa.Column("owasp", sa.Text(), nullable=True),
        sa.Column("raw", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_findings_scan_id", "findings", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_findings_scan_id", table_name="findings")
    op.drop_table("findings")
    op.drop_table("scans")

    postgresql.ENUM(name="severity").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="tool").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="scan_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="source_type").drop(op.get_bind(), checkfirst=True)
