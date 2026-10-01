"""add tenant isolation tables

Revision ID: 4f1c8a0d7b2e
Revises: e2a4309d61eb
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "4f1c8a0d7b2e"
down_revision: Union[str, Sequence[str], None] = "e2a4309d61eb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(240), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)
    op.add_column("users", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_users_tenant_id", "users", "tenants", ["tenant_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_table(
        "tenant_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tenant_documents_tenant_id", "tenant_documents", ["tenant_id"])
    op.create_table(
        "tenant_workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("workflow_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tenant_workflows_tenant_id", "tenant_workflows", ["tenant_id"])
    op.create_table(
        "tenant_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tenant_audit_logs_tenant_id", "tenant_audit_logs", ["tenant_id"])
    op.create_table(
        "tenant_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("tenant_documents.id", ondelete="CASCADE"), nullable=True),
        sa.Column("permission", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_tenant_permissions_tenant_id", "tenant_permissions", ["tenant_id"])
    op.create_index("ix_tenant_permissions_user_id", "tenant_permissions", ["user_id"])
    op.create_index("ix_tenant_permissions_document_id", "tenant_permissions", ["document_id"])


def downgrade() -> None:
    op.drop_table("tenant_permissions")
    op.drop_table("tenant_audit_logs")
    op.drop_table("tenant_workflows")
    op.drop_table("tenant_documents")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_constraint("fk_users_tenant_id", "users", type_="foreignkey")
    op.drop_column("users", "tenant_id")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
