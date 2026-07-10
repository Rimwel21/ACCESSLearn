"""merge heads

Revision ID: 3e6110e00823
Revises: 61e51b4254fa, c2a4f6b8d901
Create Date: 2026-07-10 22:24:33.374450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e6110e00823'
down_revision: Union[str, Sequence[str], None] = ('61e51b4254fa', 'c2a4f6b8d901')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
