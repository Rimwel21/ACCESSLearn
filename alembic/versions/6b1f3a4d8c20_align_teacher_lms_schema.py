"""align teacher lms schema

Revision ID: 6b1f3a4d8c20
Revises: 2395024c2591
Create Date: 2026-07-27 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision: str = "6b1f3a4d8c20"
down_revision: Union[str, Sequence[str], None] = "2395024c2591"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def _has_constraint(table_name: str, constraint_name: str) -> bool:
    if not _has_table(table_name):
        return False
    inspector = inspect(op.get_bind())
    constraints = inspector.get_unique_constraints(table_name) + inspector.get_foreign_keys(table_name)
    return any(constraint.get("name") == constraint_name for constraint in constraints)


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(index.get("name") == index_name for index in inspect(op.get_bind()).get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()

    if _has_table("teacher_modules") and not _has_column("teacher_modules", "due_at"):
        op.add_column("teacher_modules", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))

    if not _has_table("teacher_classes"):
        return

    if not _has_column("teacher_classes", "class_name"):
        op.add_column("teacher_classes", sa.Column("class_name", sa.String(length=120), nullable=True))
    if not _has_column("teacher_classes", "subject"):
        op.add_column("teacher_classes", sa.Column("subject", sa.String(length=120), nullable=True))
    if not _has_column("teacher_classes", "grade_level_id"):
        op.add_column("teacher_classes", sa.Column("grade_level_id", sa.Integer(), nullable=True))
    if not _has_column("teacher_classes", "section_id"):
        op.add_column("teacher_classes", sa.Column("section_id", sa.Integer(), nullable=True))
    if not _has_column("teacher_classes", "school_year"):
        op.add_column("teacher_classes", sa.Column("school_year", sa.String(length=30), nullable=True))

    if _has_column("teacher_classes", "grade_level"):
        bind.execute(text("""
            UPDATE teacher_classes tc
            SET grade_level_id = gl.id
            FROM grade_levels gl
            WHERE tc.grade_level_id IS NULL
              AND lower(gl.name) = lower(tc.grade_level)
        """))

    if _has_column("teacher_classes", "section"):
        bind.execute(text("""
            UPDATE teacher_classes tc
            SET section_id = hs.id
            FROM hi_sections hs
            WHERE tc.section_id IS NULL
              AND lower(hs.name) = lower(tc.section)
              AND (tc.grade_level_id IS NULL OR hs.grade_level_id = tc.grade_level_id)
        """))

        bind.execute(text("""
            UPDATE teacher_classes
            SET class_name = COALESCE(NULLIF(class_name, ''), 'Section ' || section)
            WHERE class_name IS NULL OR class_name = ''
        """))
    else:
        bind.execute(text("""
            UPDATE teacher_classes
            SET class_name = COALESCE(NULLIF(class_name, ''), 'Class')
            WHERE class_name IS NULL OR class_name = ''
        """))

    bind.execute(text("""
        UPDATE teacher_classes
        SET subject = COALESCE(NULLIF(subject, ''), 'Science'),
            student_count = COALESCE(student_count, 0)
    """))

    if not _has_index("teacher_classes", "ix_teacher_classes_grade_level_id"):
        op.create_index(op.f("ix_teacher_classes_grade_level_id"), "teacher_classes", ["grade_level_id"], unique=False)
    if not _has_index("teacher_classes", "ix_teacher_classes_section_id"):
        op.create_index(op.f("ix_teacher_classes_section_id"), "teacher_classes", ["section_id"], unique=False)

    if not _has_constraint("teacher_classes", "fk_teacher_classes_grade_level_id_grade_levels"):
        op.create_foreign_key(
            "fk_teacher_classes_grade_level_id_grade_levels",
            "teacher_classes",
            "grade_levels",
            ["grade_level_id"],
            ["id"],
        )
    if not _has_constraint("teacher_classes", "fk_teacher_classes_section_id_hi_sections"):
        op.create_foreign_key(
            "fk_teacher_classes_section_id_hi_sections",
            "teacher_classes",
            "hi_sections",
            ["section_id"],
            ["id"],
        )

    if _has_constraint("teacher_classes", "uq_teacher_class_grade_section"):
        op.drop_constraint("uq_teacher_class_grade_section", "teacher_classes", type_="unique")
    if not _has_constraint("teacher_classes", "uq_teacher_class_subject_grade_section"):
        op.create_unique_constraint(
            "uq_teacher_class_subject_grade_section",
            "teacher_classes",
            ["teacher_id", "subject", "grade_level_id", "section_id"],
        )

    op.alter_column("teacher_classes", "class_name", nullable=False)
    op.alter_column("teacher_classes", "subject", nullable=False)


def downgrade() -> None:
    if _has_constraint("teacher_classes", "uq_teacher_class_subject_grade_section"):
        op.drop_constraint("uq_teacher_class_subject_grade_section", "teacher_classes", type_="unique")
    if _has_constraint("teacher_classes", "fk_teacher_classes_section_id_hi_sections"):
        op.drop_constraint("fk_teacher_classes_section_id_hi_sections", "teacher_classes", type_="foreignkey")
    if _has_constraint("teacher_classes", "fk_teacher_classes_grade_level_id_grade_levels"):
        op.drop_constraint("fk_teacher_classes_grade_level_id_grade_levels", "teacher_classes", type_="foreignkey")
    if _has_index("teacher_classes", "ix_teacher_classes_section_id"):
        op.drop_index(op.f("ix_teacher_classes_section_id"), table_name="teacher_classes")
    if _has_index("teacher_classes", "ix_teacher_classes_grade_level_id"):
        op.drop_index(op.f("ix_teacher_classes_grade_level_id"), table_name="teacher_classes")
    if _has_column("teacher_classes", "school_year"):
        op.drop_column("teacher_classes", "school_year")
    if _has_column("teacher_classes", "section_id"):
        op.drop_column("teacher_classes", "section_id")
    if _has_column("teacher_classes", "grade_level_id"):
        op.drop_column("teacher_classes", "grade_level_id")
    if _has_column("teacher_classes", "subject"):
        op.drop_column("teacher_classes", "subject")
    if _has_column("teacher_classes", "class_name"):
        op.drop_column("teacher_classes", "class_name")
    if _has_column("teacher_modules", "due_at"):
        op.drop_column("teacher_modules", "due_at")
