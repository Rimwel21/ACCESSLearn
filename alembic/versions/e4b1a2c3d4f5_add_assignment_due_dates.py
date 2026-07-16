"""add assignment due dates

Revision ID: e4b1a2c3d4f5
Revises: 3e6110e00823
Create Date: 2026-07-15 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4b1a2c3d4f5"
down_revision: Union[str, None] = "3e6110e00823"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teacher_modules", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("teacher_assessments", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("teacher_assessments", "due_at")
    op.drop_column("teacher_modules", "due_at")
