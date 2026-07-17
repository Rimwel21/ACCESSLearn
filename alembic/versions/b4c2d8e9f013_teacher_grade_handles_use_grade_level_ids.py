"""teacher grade handles use grade level ids

Revision ID: b4c2d8e9f013
Revises: a7e04b41ceb1
Create Date: 2026-07-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b4c2d8e9f013"
down_revision: Union[str, Sequence[str], None] = "a7e04b41ceb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teacher_grade_handles", sa.Column("grade_level_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_teacher_grade_handles_grade_level_id"), "teacher_grade_handles", ["grade_level_id"], unique=False)

    op.execute(
        """
        UPDATE teacher_grade_handles AS handles
        SET grade_level_id = grade_levels.id
        FROM grade_levels
        WHERE grade_levels.name = CASE handles.grade_level_handles::text
            WHEN 'grade_1' THEN 'Grade 1'
            WHEN 'grade_2' THEN 'Grade 2'
            WHEN 'grade_3' THEN 'Grade 3'
            WHEN 'grade_4' THEN 'Grade 4'
            WHEN 'grade_5' THEN 'Grade 5'
            WHEN 'grade_6' THEN 'Grade 6'
        END
        """
    )

    op.alter_column("teacher_grade_handles", "grade_level_id", nullable=False)
    op.create_foreign_key(
        "fk_teacher_grade_handles_grade_level_id_grade_levels",
        "teacher_grade_handles",
        "grade_levels",
        ["grade_level_id"],
        ["id"],
    )
    op.drop_column("teacher_grade_handles", "grade_level_handles")


def downgrade() -> None:
    grade_level_enum = postgresql.ENUM("grade_1", "grade_2", "grade_3", "grade_4", "grade_5", "grade_6", name="gradelevel", create_type=False)
    op.add_column("teacher_grade_handles", sa.Column("grade_level_handles", grade_level_enum, nullable=True))

    op.execute(
        """
        UPDATE teacher_grade_handles AS handles
        SET grade_level_handles = CASE grade_levels.name
            WHEN 'Grade 1' THEN 'grade_1'::gradelevel
            WHEN 'Grade 2' THEN 'grade_2'::gradelevel
            WHEN 'Grade 3' THEN 'grade_3'::gradelevel
            WHEN 'Grade 4' THEN 'grade_4'::gradelevel
            WHEN 'Grade 5' THEN 'grade_5'::gradelevel
            WHEN 'Grade 6' THEN 'grade_6'::gradelevel
        END
        FROM grade_levels
        WHERE grade_levels.id = handles.grade_level_id
        """
    )

    op.alter_column("teacher_grade_handles", "grade_level_handles", nullable=False)
    op.drop_constraint("fk_teacher_grade_handles_grade_level_id_grade_levels", "teacher_grade_handles", type_="foreignkey")
    op.drop_index(op.f("ix_teacher_grade_handles_grade_level_id"), table_name="teacher_grade_handles")
    op.drop_column("teacher_grade_handles", "grade_level_id")
