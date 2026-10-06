"""add before and after snapshots to tenant audit logs

Revision ID: 9a7c2d1e4f60
Revises: c80d301df030
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a7c2d1e4f60"
down_revision: Union[str, Sequence[str], None] = "c80d301df030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant_audit_logs",
        sa.Column("old_value", sa.Text(), nullable=True),
    )
    op.add_column(
        "tenant_audit_logs",
        sa.Column("new_value", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenant_audit_logs", "new_value")
    op.drop_column("tenant_audit_logs", "old_value")
