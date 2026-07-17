"""merged

Revision ID: a7e04b41ceb1
Revises: e4b1a2c3d4f5, 7f12045064b6
Create Date: 2026-07-16 21:50:49.831720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7e04b41ceb1'
down_revision: Union[str, Sequence[str], None] = ('e4b1a2c3d4f5', '7f12045064b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
