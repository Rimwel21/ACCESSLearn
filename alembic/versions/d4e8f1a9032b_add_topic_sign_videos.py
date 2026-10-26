"""add learning topic sign-language videos

Revision ID: d4e8f1a9032b
Revises: c1a2e7d4f019
Create Date: 2026-10-26 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e8f1a9032b"
down_revision: Union[str, Sequence[str], None] = "c1a2e7d4f019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "topic_sign_videos" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "topic_sign_videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learning_topic_id", sa.Integer(), nullable=False),
        sa.Column("focus_area", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("video_url", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learning_topic_id"], ["learning_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("learning_topic_id", "focus_area", name="uq_topic_sign_video_focus"),
    )
    op.create_index("ix_topic_sign_videos_learning_topic_id", "topic_sign_videos", ["learning_topic_id"])


def downgrade() -> None:
    if "topic_sign_videos" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("topic_sign_videos")
