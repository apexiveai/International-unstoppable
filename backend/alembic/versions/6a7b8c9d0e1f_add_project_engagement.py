"""add project engagement and reputation events

Revision ID: 6a7b8c9d0e1f
Revises: 4f1c8a0d7b2e
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "6a7b8c9d0e1f"
down_revision: Union[str, Sequence[str], None] = "4f1c8a0d7b2e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_technologies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("project_id", "name", name="uq_project_technology"),
    )
    op.create_index("ix_project_technologies_project_id", "project_technologies", ["project_id"])
    for table, unique_name in [
        ("project_likes", "uq_project_like"),
        ("project_bookmarks", "uq_project_bookmark"),
        ("project_follows", "uq_project_follow"),
    ]:
        op.create_table(
            table,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("project_id", "user_id", name=unique_name),
        )
        op.create_index(f"ix_{table}_project_id", table, ["project_id"])
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])
    op.create_table(
        "project_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("vector", sa.Text(), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "reputation_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_reputation_events_user_id", "reputation_events", ["user_id"])
    op.create_index("ix_reputation_events_project_id", "reputation_events", ["project_id"])


def downgrade() -> None:
    op.drop_table("reputation_events")
    op.drop_table("project_embeddings")
    for table in ("project_follows", "project_bookmarks", "project_likes"):
        op.drop_table(table)
    op.drop_table("project_technologies")
