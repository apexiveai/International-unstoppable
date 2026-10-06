"""add parent references to forum categories

Revision ID: b38a91d6e2f4
Revises: 9a7c2d1e4f60
Create Date: 2026-10-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b38a91d6e2f4"
down_revision: Union[str, Sequence[str], None] = "9a7c2d1e4f60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("categories") as batch_op:
        batch_op.add_column(
            sa.Column(
                "parent_id",
                sa.Integer(),
                sa.ForeignKey(
                    "categories.id",
                    name="fk_categories_parent_id_categories",
                    ondelete="CASCADE",
                ),
                nullable=True,
            )
        )
        batch_op.create_index(
            op.f("ix_categories_parent_id"),
            ["parent_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("categories") as batch_op:
        batch_op.drop_index(op.f("ix_categories_parent_id"))
        batch_op.drop_column("parent_id")
