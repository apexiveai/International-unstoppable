"""add subscription billing system"""

from typing import Sequence, Union

from alembic import op

import sqlalchemy as sa

revision: str = "75b5d247d32c"

down_revision: Union[str, Sequence[str], None] = "4f1c8a0d7b2e"

branch_labels = None

depends_on = None

def upgrade() -> None:

    op.create_table(

        "subscription_plans",

        sa.Column(

            "id",

            sa.Integer(),

            primary_key=True,

        ),

        sa.Column(

            "product_key",

            sa.String(100),

            nullable=False,

        ),

        sa.Column(

            "name",

            sa.String(200),

            nullable=False,

        ),

        sa.Column(

            "description",

            sa.Text(),

            nullable=False,

            server_default="",

        ),

        sa.Column(

            "monthly_price",

            sa.Numeric(12, 2),

            nullable=False,

        ),

        sa.Column(

            "currency",

            sa.String(10),

            nullable=False,

            server_default="USD",

        ),

        sa.Column(

            "billing_cycle",

            sa.String(30),

            nullable=False,

            server_default="monthly",

        ),

        sa.Column(

            "is_active",

            sa.Boolean(),

            nullable=False,

            server_default=sa.true(),

        ),

        sa.Column(

            "created_at",

            sa.DateTime(),

            nullable=False,

            server_default=sa.func.now(),

        ),

    )

    op.create_index(

        "ix_subscription_plans_product_key",

        "subscription_plans",

        ["product_key"],

        unique=True,

    )

    op.create_table(

        "subscriptions",

        sa.Column(

            "id",

            sa.Integer(),

            primary_key=True,

        ),

        sa.Column(

            "tenant_id",

            sa.Integer(),

            nullable=False,

        ),

        sa.Column(

            "plan_id",

            sa.Integer(),

            nullable=False,

        ),

        sa.Column(

            "status",

            sa.String(30),

            nullable=False,

            server_default="active",

        ),

        sa.Column(

            "price",

            sa.Numeric(12, 2),

            nullable=False,

        ),

        sa.Column(

            "currency",

            sa.String(10),

            nullable=False,

            server_default="USD",

        ),

        sa.Column(

            "billing_cycle",

            sa.String(30),

            nullable=False,

            server_default="monthly",

        ),

        sa.Column(

            "start_date",

            sa.DateTime(),

            nullable=False,

            server_default=sa.func.now(),

        ),

        sa.Column(

            "current_period_end",

            sa.DateTime(),

            nullable=True,

        ),

        sa.Column(

            "cancelled_at",

            sa.DateTime(),

            nullable=True,

        ),

        sa.Column(

            "external_subscription_id",

            sa.String(255),

            nullable=True,

        ),

        sa.Column(

            "created_at",

            sa.DateTime(),

            nullable=False,

            server_default=sa.func.now(),

        ),

        sa.Column(

            "updated_at",

            sa.DateTime(),

            nullable=False,

            server_default=sa.func.now(),

        ),

        sa.ForeignKeyConstraint(

            ["tenant_id"],

            ["tenants.id"],

            ondelete="CASCADE",

        ),

        sa.ForeignKeyConstraint(

            ["plan_id"],

            ["subscription_plans.id"],

            ondelete="RESTRICT",

        ),

    )

    op.create_index(

        "ix_subscriptions_tenant_id",

        "subscriptions",

        ["tenant_id"],

    )

    op.create_index(

        "ix_subscriptions_plan_id",

        "subscriptions",

        ["plan_id"],

    )

    op.create_index(
        "ix_subscriptions_status",

        "subscriptions",

        ["status"],

    )

    op.create_index(

        "ix_subscriptions_external_subscription_id",

        "subscriptions",

        ["external_subscription_id"],

    )

    op.create_table(

        "billing_events",

        sa.Column(

            "id",

            sa.Integer(),

            primary_key=True,

        ),

        sa.Column(

            "tenant_id",

            sa.Integer(),

            nullable=False,

        ),

        sa.Column(

            "subscription_id",

            sa.Integer(),

            nullable=True,

        ),

        sa.Column(

            "event_type",

            sa.String(100),

            nullable=False,

        ),

        sa.Column(

            "status",

            sa.String(50),

            nullable=False,

            server_default="received",

        ),

        sa.Column(

            "external_event_id",

            sa.String(255),

            nullable=True,

        ),

        sa.Column(

            "amount",

            sa.Numeric(12, 2),

            nullable=True,

        ),

        sa.Column(

            "currency",

            sa.String(10),

            nullable=False,

            server_default="USD",

        ),

        sa.Column(

            "details",

            sa.Text(),

            nullable=False,

            server_default="",

        ),

        sa.Column(

            "created_at",

            sa.DateTime(),

            nullable=False,

            server_default=sa.func.now(),

        ),

        sa.ForeignKeyConstraint(

            ["tenant_id"],

            ["tenants.id"],

            ondelete="CASCADE",

        ),

        sa.ForeignKeyConstraint(

            ["subscription_id"],

            ["subscriptions.id"],

            ondelete="SET NULL",

        ),

    )

    op.create_index(

        "ix_billing_events_tenant_id",

        "billing_events",

        ["tenant_id"],

    )

    op.create_index(

        "ix_billing_events_subscription_id",

        "billing_events",

        ["subscription_id"],

    )

    op.create_index(

        "ix_billing_events_event_type",

        "billing_events",

        ["event_type"],

    )

    op.create_index(

        "ix_billing_events_external_event_id",

        "billing_events",

        ["external_event_id"],

        unique=True,

    )

def downgrade() -> None:

    op.drop_index(

        "ix_billing_events_external_event_id",

        table_name="billing_events",

    )

    op.drop_index(

        "ix_billing_events_event_type",

        table_name="billing_events",

    )

    op.drop_index(

        "ix_billing_events_subscription_id",

        table_name="billing_events",

    )

    op.drop_index(

        "ix_billing_events_tenant_id",

        table_name="billing_events",

    )

    op.drop_table("billing_events")

    op.drop_index(

        "ix_subscriptions_external_subscription_id",

        table_name="subscriptions",

    )

    op.drop_index(

        "ix_subscriptions_status",

        table_name="subscriptions",

    )

    op.drop_index(

        "ix_subscriptions_plan_id",

        table_name="subscriptions",

    )

    op.drop_index(

        "ix_subscriptions_tenant_id",

        table_name="subscriptions",

    )

    op.drop_table("subscriptions")

    op.drop_index(

        "ix_subscription_plans_product_key",

        table_name="subscription_plans",

    )

    op.drop_table("subscription_plans")