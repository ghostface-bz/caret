"""add finding fingerprint + triage (status/note/triaged_at)

Revision ID: 0003_finding_triage
Revises: 0002_scan_content_hash
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_finding_triage"
down_revision: Union[str, None] = "0002_scan_content_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    triage_status = postgresql.ENUM(
        "open", "false_positive", "resolved", "suppressed",
        name="triage_status", create_type=False,
    )
    triage_status.create(op.get_bind(), checkfirst=True)

    op.add_column("findings", sa.Column("fingerprint", sa.Text(), nullable=True))
    op.add_column(
        "findings",
        sa.Column("triage_status", triage_status, nullable=False, server_default="open"),
    )
    op.add_column("findings", sa.Column("triage_note", sa.Text(), nullable=True))
    op.add_column(
        "findings", sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_findings_fingerprint", "findings", ["fingerprint"])

    # Backfill fingerprint for existing rows — MUST match models.finding_fingerprint:
    # md5(tool:rule_id:file_path:line_start), with '' for a NULL line_start.
    op.execute(
        """
        UPDATE findings
        SET fingerprint = md5(
            tool::text || ':' || rule_id || ':' || file_path || ':' ||
            coalesce(line_start::text, '')
        )
        WHERE fingerprint IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_findings_fingerprint", table_name="findings")
    op.drop_column("findings", "triaged_at")
    op.drop_column("findings", "triage_note")
    op.drop_column("findings", "triage_status")
    op.drop_column("findings", "fingerprint")
    postgresql.ENUM(name="triage_status").drop(op.get_bind(), checkfirst=True)
