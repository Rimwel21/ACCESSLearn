"""backend test compatibility stamp

Revision ID: 9b1d2c3e4f50
Revises: 6f702856c187
Create Date: 2026-07-03 00:00:00.000000

"""
from typing import Sequence, Union


revision: str = "9b1d2c3e4f50"
down_revision: Union[str, Sequence[str], None] = "6f702856c187"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Compatibility marker for databases previously stamped by backend-test."""


def downgrade() -> None:
    """Compatibility marker only; no schema changes to reverse."""
