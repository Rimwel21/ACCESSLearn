"""add lms and handsign support

Revision ID: a7c9e2d4f601
Revises: 9b1d2c3e4f50
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "a7c9e2d4f601"
down_revision: Union[str, Sequence[str], None] = "9b1d2c3e4f50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def upgrade() -> None:
    if all(_has_table(table) for table in (
        "teacher_classes",
        "teacher_modules",
        "learning_topics",
        "teacher_assessments",
        "student_topic_progress",
        "student_quiz_progress",
    )):
        return

    if not _has_table("teacher_classes"):
        _create_teacher_classes()
    if not _has_table("teacher_modules"):
        _create_teacher_modules()
    if not _has_table("learning_topics"):
        _create_learning_topics()
    if not _has_table("teacher_assessments"):
        _create_teacher_assessments()
    if not _has_table("student_topic_progress"):
        _create_student_topic_progress()
    if not _has_table("student_quiz_progress"):
        _create_student_quiz_progress()


def _create_teacher_classes() -> None:
    op.create_table(
        "teacher_classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("grade_level", sa.String(length=30), nullable=False),
        sa.Column("section", sa.String(length=50), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "grade_level", "section", name="uq_teacher_class_grade_section"),
    )
    op.create_index(op.f("ix_teacher_classes_id"), "teacher_classes", ["id"], unique=False)
    op.create_index(op.f("ix_teacher_classes_teacher_id"), "teacher_classes", ["teacher_id"], unique=False)


def _create_teacher_modules() -> None:
    op.create_table(
        "teacher_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=60), nullable=True),
        sa.Column("week", sa.String(length=30), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_type", sa.String(length=120), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("behavior_required", sa.String(length=10), nullable=False, server_default="true"),
        sa.Column("estimated_time", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["teacher_classes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["teacher_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teacher_modules_class_id"), "teacher_modules", ["class_id"], unique=False)
    op.create_index(op.f("ix_teacher_modules_id"), "teacher_modules", ["id"], unique=False)
    op.create_index(op.f("ix_teacher_modules_teacher_id"), "teacher_modules", ["teacher_id"], unique=False)


def _create_learning_topics() -> None:
    op.create_table(
        "learning_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("page_image_urls", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["teacher_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_topics_id"), "learning_topics", ["id"], unique=False)
    op.create_index(op.f("ix_learning_topics_module_id"), "learning_topics", ["module_id"], unique=False)
    op.alter_column("learning_topics", "page_image_urls", server_default=None)


def _create_teacher_assessments() -> None:
    op.create_table(
        "teacher_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("assessment_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("week", sa.String(length=30), nullable=True),
        sa.Column("time_limit", sa.String(length=30), nullable=True),
        sa.Column("attempts_allowed", sa.Integer(), nullable=False),
        sa.Column("shuffle_questions", sa.String(length=10), nullable=False),
        sa.Column("show_answers_after_submission", sa.String(length=10), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["teacher_modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teacher_assessments_assessment_type"), "teacher_assessments", ["assessment_type"], unique=False)
    op.create_index(op.f("ix_teacher_assessments_id"), "teacher_assessments", ["id"], unique=False)
    op.create_index(op.f("ix_teacher_assessments_module_id"), "teacher_assessments", ["module_id"], unique=False)
    op.create_index(op.f("ix_teacher_assessments_teacher_id"), "teacher_assessments", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_teacher_assessments_topic_id"), "teacher_assessments", ["topic_id"], unique=False)


def _create_student_topic_progress() -> None:
    op.create_table(
        "student_topic_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["teacher_modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "topic_id", name="uq_student_topic_progress"),
    )
    op.create_index(op.f("ix_student_topic_progress_id"), "student_topic_progress", ["id"], unique=False)
    op.create_index(op.f("ix_student_topic_progress_module_id"), "student_topic_progress", ["module_id"], unique=False)
    op.create_index(op.f("ix_student_topic_progress_student_id"), "student_topic_progress", ["student_id"], unique=False)
    op.create_index(op.f("ix_student_topic_progress_topic_id"), "student_topic_progress", ["topic_id"], unique=False)


def _create_student_quiz_progress() -> None:
    op.create_table(
        "student_quiz_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["teacher_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["teacher_modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "assessment_id", name="uq_student_quiz_progress"),
    )
    op.create_index(op.f("ix_student_quiz_progress_assessment_id"), "student_quiz_progress", ["assessment_id"], unique=False)
    op.create_index(op.f("ix_student_quiz_progress_id"), "student_quiz_progress", ["id"], unique=False)
    op.create_index(op.f("ix_student_quiz_progress_module_id"), "student_quiz_progress", ["module_id"], unique=False)
    op.create_index(op.f("ix_student_quiz_progress_student_id"), "student_quiz_progress", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_student_quiz_progress_student_id"), table_name="student_quiz_progress")
    op.drop_index(op.f("ix_student_quiz_progress_module_id"), table_name="student_quiz_progress")
    op.drop_index(op.f("ix_student_quiz_progress_id"), table_name="student_quiz_progress")
    op.drop_index(op.f("ix_student_quiz_progress_assessment_id"), table_name="student_quiz_progress")
    op.drop_table("student_quiz_progress")
    op.drop_index(op.f("ix_student_topic_progress_topic_id"), table_name="student_topic_progress")
    op.drop_index(op.f("ix_student_topic_progress_student_id"), table_name="student_topic_progress")
    op.drop_index(op.f("ix_student_topic_progress_module_id"), table_name="student_topic_progress")
    op.drop_index(op.f("ix_student_topic_progress_id"), table_name="student_topic_progress")
    op.drop_table("student_topic_progress")
    op.drop_index(op.f("ix_teacher_assessments_topic_id"), table_name="teacher_assessments")
    op.drop_index(op.f("ix_teacher_assessments_teacher_id"), table_name="teacher_assessments")
    op.drop_index(op.f("ix_teacher_assessments_module_id"), table_name="teacher_assessments")
    op.drop_index(op.f("ix_teacher_assessments_id"), table_name="teacher_assessments")
    op.drop_index(op.f("ix_teacher_assessments_assessment_type"), table_name="teacher_assessments")
    op.drop_table("teacher_assessments")
    op.drop_index(op.f("ix_learning_topics_module_id"), table_name="learning_topics")
    op.drop_index(op.f("ix_learning_topics_id"), table_name="learning_topics")
    op.drop_table("learning_topics")
    op.drop_index(op.f("ix_teacher_modules_teacher_id"), table_name="teacher_modules")
    op.drop_index(op.f("ix_teacher_modules_id"), table_name="teacher_modules")
    op.drop_index(op.f("ix_teacher_modules_class_id"), table_name="teacher_modules")
    op.drop_table("teacher_modules")
    op.drop_index(op.f("ix_teacher_classes_teacher_id"), table_name="teacher_classes")
    op.drop_index(op.f("ix_teacher_classes_id"), table_name="teacher_classes")
    op.drop_table("teacher_classes")
