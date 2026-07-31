"""add quiz timer seconds

Revision ID: 9d87e2b4c6a1
Revises: 6b1f3a4d8c20
Create Date: 2026-07-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from alembic import context
import sqlalchemy as sa


revision: str = "9d87e2b4c6a1"
down_revision: Union[str, Sequence[str], None] = "6b1f3a4d8c20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _add_column_if_missing("teacher_assessments", sa.Column("time_limit_seconds", sa.Integer(), nullable=True))
    _add_column_if_missing("student_quiz_progress", sa.Column("time_limit_seconds", sa.Integer(), nullable=True))
    _add_column_if_missing("student_quiz_progress", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("student_quiz_progress", sa.Column("submission_type", sa.String(length=20), nullable=True))
    op.alter_column("student_quiz_progress", "started_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    if context.is_offline_mode():
        return

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, time_limit FROM teacher_assessments WHERE time_limit IS NOT NULL")).fetchall()
    for row in rows:
        seconds = _parse_time_limit_seconds(row.time_limit)
        if seconds:
            connection.execute(
                sa.text("UPDATE teacher_assessments SET time_limit_seconds = :seconds WHERE id = :id"),
                {"seconds": seconds, "id": row.id},
            )


def downgrade() -> None:
    op.alter_column("student_quiz_progress", "started_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    _drop_column_if_exists("student_quiz_progress", "submission_type")
    _drop_column_if_exists("student_quiz_progress", "expires_at")
    _drop_column_if_exists("student_quiz_progress", "time_limit_seconds")
    _drop_column_if_exists("teacher_assessments", "time_limit_seconds")


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if context.is_offline_mode():
        op.add_column(table_name, column)
        return
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table_name)}
    if column.name not in columns:
        op.add_column(table_name, column)


def _drop_column_if_exists(table_name: str, column_name: str) -> None:
    if context.is_offline_mode():
        op.drop_column(table_name, column_name)
        return
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table_name)}
    if column_name in columns:
        op.drop_column(table_name, column_name)


def _parse_time_limit_seconds(value: str | None) -> int | None:
    if not value:
        return None
    parts = value.strip().lower().split()
    if not parts or not parts[0].isdigit():
        return None
    amount = int(parts[0])
    if amount <= 0:
        return None
    unit = parts[1] if len(parts) > 1 else "seconds"
    if unit.startswith("hour"):
        return amount * 3600
    if unit.startswith("minute"):
        return amount * 60
    if unit.startswith("second"):
        return amount
    return None
