"""merge subscription and project engagement migrations

Revision ID: 626dfb4ca5f2
Revises: 6a7b8c9d0e1f, 75b5d247d32c
Create Date: 2026-09-27 22:23:54.904559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '626dfb4ca5f2'
down_revision: Union[str, Sequence[str], None] = ('6a7b8c9d0e1f', '75b5d247d32c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
