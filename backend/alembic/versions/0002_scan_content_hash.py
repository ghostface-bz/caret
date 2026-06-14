"""add scans.content_hash (content-hash scan cache)

Revision ID: 0002_scan_content_hash
Revises: 0001_initial
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_scan_content_hash"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("content_hash", sa.Text(), nullable=True))
    op.create_index("ix_scans_content_hash", "scans", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_scans_content_hash", table_name="scans")
    op.drop_column("scans", "content_hash")
