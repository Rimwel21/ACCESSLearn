"""add handsign tutorial practice

Revision ID: b8a2c5f41d90
Revises: 9d87e2b4c6a1
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8a2c5f41d90"
down_revision: Union[str, Sequence[str], None] = "9d87e2b4c6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "handsign_tutorial_practice" in inspector.get_table_names():
        return

    op.create_table(
        "handsign_tutorial_practice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("progress_id", sa.Integer(), nullable=True),
        sa.Column("canonical_word", sa.String(length=80), nullable=False),
        sa.Column("attempt_scores", sa.JSON(), nullable=False),
        sa.Column("highest_score", sa.Float(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["teacher_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["progress_id"], ["student_quiz_progress.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "activity_id", "canonical_word", name="uq_handsign_tutorial_practice"),
    )
    op.create_index(op.f("ix_handsign_tutorial_practice_id"), "handsign_tutorial_practice", ["id"], unique=False)
    op.create_index(op.f("ix_handsign_tutorial_practice_student_id"), "handsign_tutorial_practice", ["student_id"], unique=False)
    op.create_index(op.f("ix_handsign_tutorial_practice_activity_id"), "handsign_tutorial_practice", ["activity_id"], unique=False)
    op.create_index(op.f("ix_handsign_tutorial_practice_progress_id"), "handsign_tutorial_practice", ["progress_id"], unique=False)
    op.create_index(op.f("ix_handsign_tutorial_practice_canonical_word"), "handsign_tutorial_practice", ["canonical_word"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "handsign_tutorial_practice" not in inspector.get_table_names():
        return

    op.drop_index(op.f("ix_handsign_tutorial_practice_canonical_word"), table_name="handsign_tutorial_practice")
    op.drop_index(op.f("ix_handsign_tutorial_practice_progress_id"), table_name="handsign_tutorial_practice")
    op.drop_index(op.f("ix_handsign_tutorial_practice_activity_id"), table_name="handsign_tutorial_practice")
    op.drop_index(op.f("ix_handsign_tutorial_practice_student_id"), table_name="handsign_tutorial_practice")
    op.drop_index(op.f("ix_handsign_tutorial_practice_id"), table_name="handsign_tutorial_practice")
    op.drop_table("handsign_tutorial_practice")
