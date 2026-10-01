"""add users and thread authors

Revision ID: 3d8251495145

Revises: PREVIOUS_REVISION_ID

Create Date: 2026-09-15

"""

from alembic import op

import sqlalchemy as sa

revision = "3d8251495145"

down_revision = "d9548e904462"

branch_labels = None

depends_on = None

def upgrade() -> None:

    # 1. Create users table

    op.create_table(

        "users",

        sa.Column("id", sa.Integer(), nullable=False),

        sa.Column(

            "username",

            sa.String(length=50),

            nullable=False,

        ),

        sa.Column(

            "email",

            sa.String(length=255),

            nullable=False,

        ),

        sa.Column(

            "password_hash",

            sa.String(length=255),

            nullable=False,

        ),

        sa.Column(

            "display_name",

            sa.String(length=100),

            nullable=False,

        ),

        sa.Column(

            "bio",

            sa.String(length=500),

            nullable=False,

        ),

        sa.Column(

            "is_active",

            sa.Boolean(),

            nullable=False,

        ),

        sa.Column(

            "is_admin",

            sa.Boolean(),

            nullable=False,

        ),

        sa.Column(

            "created_at",

            sa.DateTime(),

            nullable=False,

        ),

        sa.PrimaryKeyConstraint("id"),

    )

    op.create_index(

        "ix_users_email",

        "users",

        ["email"],

        unique=True,

    )

    op.create_index(

        "ix_users_username",

        "users",

        ["username"],

        unique=True,

    )

    # 2. Add author_id temporarily nullable

    op.add_column(

        "threads",

        sa.Column(

            "author_id",

            sa.Integer(),

            nullable=True,

        ),

    )

    op.create_index(

        "ix_threads_author_id",

        "threads",

        ["author_id"],

        unique=False,

    )

    op.create_foreign_key(

        "fk_threads_author_id_users",

        "threads",

        "users",

        ["author_id"],

        ["id"],

    )

    # 3. Create system user for existing threads

    op.execute(

        """

        INSERT INTO users (

            username,

            email,

            password_hash,

            display_name,

            bio,

            is_active,

            is_admin,

            created_at

        )

        VALUES (

            'system',

            'system@apexive.local',

            'SYSTEM_ACCOUNT_NO_LOGIN',

            'Apexive Community',

            'System account for migrated content.',

            true,

            true,

            NOW()

        )

        """

    )

    # 4. Backfill existing threads

    op.execute(

        """

        UPDATE threads

        SET author_id = (

            SELECT id

            FROM users

            WHERE username = 'system'

        )

        WHERE author_id IS NULL

        """

    )

    # 5. Now enforce NOT NULL

    op.alter_column(

        "threads",

        "author_id",

        existing_type=sa.Integer(),

        nullable=False,

    )

def downgrade() -> None:

    op.drop_constraint(

        "fk_threads_author_id_users",

        "threads",

        type_="foreignkey",

    )

    op.drop_index(

        "ix_threads_author_id",

        table_name="threads",

    )

    op.drop_column(

        "threads",

        "author_id",

    )

    op.drop_index(

        "ix_users_username",

        table_name="users",

    )

    op.drop_index(

        "ix_users_email",

        table_name="users",

    )

    op.drop_table("users")