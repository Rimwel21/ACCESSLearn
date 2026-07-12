"""add class metadata

Revision ID: b8d2f4a9c731
Revises: a7c9e2d4f601
Create Date: 2026-07-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8d2f4a9c731"
down_revision: Union[str, Sequence[str], None] = "a7c9e2d4f601"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "teacher_classes",
        sa.Column("class_name", sa.String(length=120), nullable=False, server_default="Class"),
    )
    op.add_column(
        "teacher_classes",
        sa.Column("subject", sa.String(length=120), nullable=False, server_default="General"),
    )
    op.add_column("teacher_classes", sa.Column("school_year", sa.String(length=30), nullable=True))
    op.drop_constraint("uq_teacher_class_grade_section", "teacher_classes", type_="unique")
    op.create_unique_constraint(
        "uq_teacher_class_subject_grade_section",
        "teacher_classes",
        ["teacher_id", "subject", "grade_level", "section"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_teacher_class_subject_grade_section", "teacher_classes", type_="unique")
    op.create_unique_constraint(
        "uq_teacher_class_grade_section",
        "teacher_classes",
        ["teacher_id", "grade_level", "section"],
    )
    op.drop_column("teacher_classes", "school_year")
    op.drop_column("teacher_classes", "subject")
    op.drop_column("teacher_classes", "class_name")
