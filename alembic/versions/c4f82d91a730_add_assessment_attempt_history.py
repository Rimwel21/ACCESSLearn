"""add assessment attempt history

Revision ID: c4f82d91a730
Revises: b8a2c5f41d90
Create Date: 2026-10-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "c4f82d91a730"
down_revision: Union[str, Sequence[str], None] = "b8a2c5f41d90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column("student_quiz_progress", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
        op.add_column("student_quiz_progress", sa.Column("attempt_history", sa.JSON(), server_default="[]", nullable=False))
        return

    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("student_quiz_progress")}
    if "attempt_count" not in columns:
        op.add_column("student_quiz_progress", sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False))
    if "attempt_history" not in columns:
        op.add_column("student_quiz_progress", sa.Column("attempt_history", sa.JSON(), server_default="[]", nullable=False))
    op.execute(
        "UPDATE student_quiz_progress SET attempt_count = 1 "
        "WHERE status = 'completed' AND attempt_count = 0"
    )


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_column("student_quiz_progress", "attempt_history")
        op.drop_column("student_quiz_progress", "attempt_count")
        return

    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("student_quiz_progress")}
    if "attempt_history" in columns:
        op.drop_column("student_quiz_progress", "attempt_history")
    if "attempt_count" in columns:
        op.drop_column("student_quiz_progress", "attempt_count")
