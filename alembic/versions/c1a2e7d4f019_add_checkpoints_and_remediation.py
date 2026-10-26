"""add learning checkpoints and targeted remediation

Revision ID: c1a2e7d4f019
Revises: b8a2c5f41d90
Create Date: 2026-10-22 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a2e7d4f019"
down_revision: Union[str, Sequence[str], None] = "b8a2c5f41d90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())
    if "module_checkpoints" not in existing:
        op.create_table(
            "module_checkpoints",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("module_id", sa.Integer(), nullable=False),
            sa.Column("start_sort_order", sa.Integer(), nullable=False),
            sa.Column("end_sort_order", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("questions", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["module_id"], ["teacher_modules.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("module_id", "start_sort_order", name="uq_module_checkpoint_start"),
        )
        op.create_index("ix_module_checkpoints_module_id", "module_checkpoints", ["module_id"])
    if "student_checkpoint_attempts" not in existing:
        op.create_table(
            "student_checkpoint_attempts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("checkpoint_id", sa.Integer(), nullable=False),
            sa.Column("answers", sa.JSON(), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("total", sa.Integer(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["student_id"], ["accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["checkpoint_id"], ["module_checkpoints.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("student_id", "checkpoint_id", name="uq_student_checkpoint_attempt"),
        )
        op.create_index("ix_student_checkpoint_attempts_student_id", "student_checkpoint_attempts", ["student_id"])
        op.create_index("ix_student_checkpoint_attempts_checkpoint_id", "student_checkpoint_attempts", ["checkpoint_id"])
    if "student_module_learning_summaries" not in existing:
        op.create_table(
            "student_module_learning_summaries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("module_id", sa.Integer(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("teacher_notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["student_id"], ["accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["module_id"], ["teacher_modules.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("student_id", "module_id", name="uq_student_module_learning_summary"),
        )
    if "remediation_activities" not in existing:
        op.create_table(
            "remediation_activities",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("teacher_id", sa.Integer(), nullable=False),
            sa.Column("module_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["teacher_id"], ["accounts.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["module_id"], ["teacher_modules.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "remediation_interventions" not in existing:
        op.create_table(
            "remediation_interventions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("remediation_activity_id", sa.Integer(), nullable=False),
            sa.Column("checkpoint_id", sa.Integer(), nullable=True),
            sa.Column("start_sort_order", sa.Integer(), nullable=False),
            sa.Column("end_sort_order", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("instructions", sa.String(length=2000), nullable=True),
            sa.Column("questions", sa.JSON(), nullable=False),
            sa.Column("video_url", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["remediation_activity_id"], ["remediation_activities.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["checkpoint_id"], ["module_checkpoints.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "remediation_targets" not in existing:
        op.create_table(
            "remediation_targets",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("intervention_id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("answers", sa.JSON(), nullable=False),
            sa.Column("score", sa.Integer(), nullable=True),
            sa.Column("total", sa.Integer(), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["intervention_id"], ["remediation_interventions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["student_id"], ["accounts.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("intervention_id", "student_id", name="uq_remediation_target"),
        )


def downgrade() -> None:
    for name in ("remediation_targets", "remediation_interventions", "remediation_activities", "student_module_learning_summaries", "student_checkpoint_attempts", "module_checkpoints"):
        if name in sa.inspect(op.get_bind()).get_table_names():
            op.drop_table(name)
