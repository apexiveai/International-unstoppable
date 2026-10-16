"""Add RPA license plans, licenses, activations and audit events."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c21b74d6f90"
down_revision: Union[str, Sequence[str], None] = "39c4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "license_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False, unique=True),
        sa.Column("description", sa.String(length=2000), nullable=False, server_default=""),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("max_robots", sa.Integer(), nullable=False),
        sa.Column("max_workflows", sa.Integer(), nullable=False),
        sa.Column("max_activations", sa.Integer(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "licenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="unassigned"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_id"], ["license_plans.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
    )
    op.create_index("ix_licenses_key_hash", "licenses", ["key_hash"], unique=True)
    op.create_index("ix_licenses_tenant_id", "licenses", ["tenant_id"])
    op.create_index("ix_licenses_plan_id", "licenses", ["plan_id"])
    op.create_index("ix_licenses_status", "licenses", ["status"])
    op.create_index("ix_licenses_expires_at", "licenses", ["expires_at"])

    op.create_table(
        "license_activations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("license_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_by_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deactivated_by_id"], ["users.id"]),
    )
    op.create_index(
        "ix_license_activations_license_id", "license_activations", ["license_id"]
    )
    op.create_index(
        "ix_license_activations_device_id", "license_activations", ["device_id"]
    )
    op.create_index(
        "ix_license_activations_is_active", "license_activations", ["is_active"]
    )
    op.create_table(
        "license_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("license_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["license_id"], ["licenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_license_events_license_id", "license_events", ["license_id"])
    op.create_index("ix_license_events_actor_user_id", "license_events", ["actor_user_id"])
    op.create_index("ix_license_events_event_type", "license_events", ["event_type"])
    op.create_index("ix_license_events_created_at", "license_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_license_events_created_at", table_name="license_events")
    op.drop_index("ix_license_events_event_type", table_name="license_events")
    op.drop_index("ix_license_events_actor_user_id", table_name="license_events")
    op.drop_index("ix_license_events_license_id", table_name="license_events")
    op.drop_table("license_events")
    op.drop_index("ix_license_activations_is_active", table_name="license_activations")
    op.drop_index("ix_license_activations_device_id", table_name="license_activations")
    op.drop_index("ix_license_activations_license_id", table_name="license_activations")
    op.drop_table("license_activations")
    op.drop_index("ix_licenses_expires_at", table_name="licenses")
    op.drop_index("ix_licenses_status", table_name="licenses")
    op.drop_index("ix_licenses_plan_id", table_name="licenses")
    op.drop_index("ix_licenses_tenant_id", table_name="licenses")
    op.drop_index("ix_licenses_key_hash", table_name="licenses")
    op.drop_table("licenses")
    op.drop_table("license_plans")
