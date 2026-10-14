"""Add system-level audit events."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.String(length=100), nullable=True),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("details", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_system_audit_events_tenant_id",
        "system_audit_events",
        ["tenant_id"],
    )
    op.create_index(
        "ix_system_audit_events_actor_user_id",
        "system_audit_events",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_system_audit_events_action",
        "system_audit_events",
        ["action"],
    )


def downgrade() -> None:
    op.drop_index("ix_system_audit_events_action", table_name="system_audit_events")
    op.drop_index(
        "ix_system_audit_events_actor_user_id",
        table_name="system_audit_events",
    )
    op.drop_index(
        "ix_system_audit_events_tenant_id",
        table_name="system_audit_events",
    )
    op.drop_table("system_audit_events")
