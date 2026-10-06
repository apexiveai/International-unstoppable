"""add notifications and workflow execution tables

Revision ID: a1b2c3d4e5f6
Revises: b38a91d6e2f4
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "b38a91d6e2f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_id", sa.Integer(), nullable=False),
        sa.Column("workflow_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("current_step", sa.String(length=100), nullable=False),
        sa.Column("input_payload", sa.Text(), nullable=False),
        sa.Column("result_payload", sa.Text(), nullable=False),
        sa.Column("checkpoint", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_executions_status",
        "workflow_executions",
        ["status"],
    )
    op.create_index(
        "ix_workflow_executions_tenant_id",
        "workflow_executions",
        ["tenant_id"],
    )

    op.create_table(
        "workflow_execution_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("execution_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["workflow_executions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_execution_events_execution_id",
        "workflow_execution_events",
        ["execution_id"],
    )
    op.create_index(
        "ix_workflow_execution_events_tenant_id",
        "workflow_execution_events",
        ["tenant_id"],
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.String(length=500), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_recipient_id",
        "notifications",
        ["recipient_id"],
    )
    op.create_index("ix_notifications_actor_id", "notifications", ["actor_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index(
        "ix_tenant_documents_owner_id",
        "tenant_documents",
        ["owner_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_documents_owner_id", table_name="tenant_documents")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_actor_id", table_name="notifications")
    op.drop_index("ix_notifications_recipient_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(
        "ix_workflow_execution_events_tenant_id",
        table_name="workflow_execution_events",
    )
    op.drop_index(
        "ix_workflow_execution_events_execution_id",
        table_name="workflow_execution_events",
    )
    op.drop_table("workflow_execution_events")
    op.drop_index(
        "ix_workflow_executions_tenant_id",
        table_name="workflow_executions",
    )
    op.drop_index(
        "ix_workflow_executions_status",
        table_name="workflow_executions",
    )
    op.drop_table("workflow_executions")
