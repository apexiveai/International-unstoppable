"""Add user role and account approval fields used by the API."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            server_default="USER",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "account_status",
            sa.String(length=30),
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.add_column(
        "users",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("approved_by", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "approved_by")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "account_status")
    op.drop_column("users", "role")
