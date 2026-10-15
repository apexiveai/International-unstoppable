"""Add product entitlement codes, trademark contracts and check history."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "39c4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "f9e8d7c6b5a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscription_plans",
        sa.Column("code", sa.String(length=100), nullable=True),
    )
    op.execute(
        "UPDATE subscription_plans "
        "SET code = CASE product_key "
        "WHEN 'trademark' THEN 'TRADEMARK_CONFLICT' "
        "WHEN 'workforce' THEN 'AUTONOMOUS_WORKFORCE' "
        "WHEN 'max_myanmar' THEN 'MAX_MYANMAR' "
        "WHEN 'mna' THEN 'MNA_AIRLINES' "
        "ELSE UPPER(product_key) END"
    )
    op.alter_column("subscription_plans", "code", nullable=False)
    op.create_index(
        "ix_subscription_plans_code",
        "subscription_plans",
        ["code"],
        unique=True,
    )

    op.add_column(
        "subscriptions",
        sa.Column("contract_months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("contract_end", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "trademark_conflict_checks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("comparison_filename", sa.String(length=255), nullable=False),
        sa.Column("result_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_trademark_conflict_checks_tenant_id",
        "trademark_conflict_checks",
        ["tenant_id"],
    )
    op.create_index(
        "ix_trademark_conflict_checks_user_id",
        "trademark_conflict_checks",
        ["user_id"],
    )
    op.create_index(
        "ix_trademark_conflict_checks_created_at",
        "trademark_conflict_checks",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_trademark_conflict_checks_created_at",
        table_name="trademark_conflict_checks",
    )
    op.drop_index(
        "ix_trademark_conflict_checks_user_id",
        table_name="trademark_conflict_checks",
    )
    op.drop_index(
        "ix_trademark_conflict_checks_tenant_id",
        table_name="trademark_conflict_checks",
    )
    op.drop_table("trademark_conflict_checks")
    op.drop_column("subscriptions", "contract_end")
    op.drop_column("subscriptions", "contract_months")
    op.drop_index("ix_subscription_plans_code", table_name="subscription_plans")
    op.drop_column("subscription_plans", "code")
