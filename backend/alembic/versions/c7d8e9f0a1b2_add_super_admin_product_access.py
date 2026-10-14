"""Add Super Admin product grants and one-time launch codes."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_super_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_table(
        "tenant_product_access_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_key", sa.String(length=100), nullable=False),
        sa.Column("access_type", sa.String(length=30), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_permanent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("granted_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "(is_permanent AND expires_at IS NULL) OR "
            "(NOT is_permanent AND expires_at IS NOT NULL)",
            name="ck_tenant_product_grants_permanent_expiration",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["granted_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["revoked_by_id"], ["users.id"]),
    )
    op.create_index(
        "ix_tenant_product_access_grants_tenant_id",
        "tenant_product_access_grants",
        ["tenant_id"],
    )
    op.create_index(
        "ix_tenant_product_access_grants_product_key",
        "tenant_product_access_grants",
        ["product_key"],
    )
    op.create_table(
        "product_launch_codes",
        sa.Column("code_hash", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_key", sa.String(length=100), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_product_launch_codes_user_id", "product_launch_codes", ["user_id"]
    )
    op.create_index(
        "ix_product_launch_codes_tenant_id", "product_launch_codes", ["tenant_id"]
    )
    op.add_column(
        "product_launch_codes",
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "product_launch_codes",
        sa.Column("revoked_by_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_product_launch_codes_revoked_by_id_users",
        "product_launch_codes",
        "users",
        ["revoked_by_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_product_launch_codes_revoked_by_id_users",
        "product_launch_codes",
        type_="foreignkey",
    )
    op.drop_column("product_launch_codes", "revoked_by_id")
    op.drop_column("product_launch_codes", "revoked_at")
    op.drop_index("ix_product_launch_codes_tenant_id", table_name="product_launch_codes")
    op.drop_index("ix_product_launch_codes_user_id", table_name="product_launch_codes")
    op.drop_table("product_launch_codes")
    op.drop_index(
        "ix_tenant_product_access_grants_product_key",
        table_name="tenant_product_access_grants",
    )
    op.drop_index(
        "ix_tenant_product_access_grants_tenant_id",
        table_name="tenant_product_access_grants",
    )
    op.drop_table("tenant_product_access_grants")
    op.drop_column("users", "is_super_admin")
