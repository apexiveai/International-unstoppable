"""add thread detail fields

Revision ID: c80d301df030
Revises: 78de6e9dccc7
Create Date: 2026-09-29 14:09:24.739339

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c80d301df030"
down_revision: Union[str, Sequence[str], None] = "78de6e9dccc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add thread detail fields."""

    op.add_column(
        "threads",
        sa.Column("problem", sa.Text(), nullable=True),
    )

    op.add_column(
        "threads",
        sa.Column("network_environment", sa.Text(), nullable=True),
    )

    op.add_column(
        "threads",
        sa.Column("symptoms", sa.Text(), nullable=True),
    )

    op.add_column(
        "threads",
        sa.Column("logs_alarms", sa.Text(), nullable=True),
    )

    op.add_column(
        "threads",
        sa.Column("what_i_tried", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove thread detail fields."""

    op.drop_column("threads", "what_i_tried")
    op.drop_column("threads", "logs_alarms")
    op.drop_column("threads", "symptoms")
    op.drop_column("threads", "network_environment")
    op.drop_column("threads", "problem")
