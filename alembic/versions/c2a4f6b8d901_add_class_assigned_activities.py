"""add class assigned activities

Revision ID: c2a4f6b8d901
Revises: b8d2f4a9c731
Create Date: 2026-07-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2a4f6b8d901"
down_revision: Union[str, Sequence[str], None] = "b8d2f4a9c731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("teacher_assessments", sa.Column("class_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_teacher_assessments_class_id"), "teacher_assessments", ["class_id"], unique=False)
    op.create_foreign_key(
        "fk_teacher_assessments_class_id_teacher_classes",
        "teacher_assessments",
        "teacher_classes",
        ["class_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("student_quiz_progress", "module_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("student_quiz_progress", "module_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint("fk_teacher_assessments_class_id_teacher_classes", "teacher_assessments", type_="foreignkey")
    op.drop_index(op.f("ix_teacher_assessments_class_id"), table_name="teacher_assessments")
    op.drop_column("teacher_assessments", "class_id")
