
"""No-op migration: launch-code revocation fields already exist.

The parent migration c7d8e9f0a1b2 creates revoked_at and revoked_by_id
on product_launch_codes. Keep this revision to preserve the existing
Alembic revision history without adding the columns twice.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
