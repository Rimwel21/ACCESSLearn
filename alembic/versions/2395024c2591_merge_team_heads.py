"""merge team heads

Revision ID: 2395024c2591
Revises: 315f96f17b70
Create Date: 2026-07-12 16:42:26.291685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2395024c2591'
down_revision: Union[str, Sequence[str], None] = '315f96f17b70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
