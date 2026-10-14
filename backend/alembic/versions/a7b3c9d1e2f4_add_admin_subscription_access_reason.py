"""add explicit admin-granted subscription access reason"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b3c9d1e2f4"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("admin_access_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "admin_access_reason")
