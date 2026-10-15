
import os
from getpass import getpass

# Set the URL before importing app settings or Alembic.
database_url = getpass(
    "Paste the NEW Render External Database URL: "
).strip()

if not database_url:
    raise SystemExit("ERROR: Database URL is required.")

os.environ["DATABASE_URL"] = database_url

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 15},
)

try:
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        current_revision = connection.execute(
            text("SELECT version_num FROM public.alembic_version")
        ).scalar_one()

        host = engine.url.host

    if database_name != "apexive_admin_eisn":
        raise SystemExit(
            f"SAFETY STOP: Unexpected database {database_name!r}"
        )

    if not host or host.lower() in {
        "localhost", "127.0.0.1", "::1"
    }:
        raise SystemExit("SAFETY STOP: Not a remote database.")

    print("\nProduction database verified.")
    print("Database:", database_name)
    print("Host:", host)
    print("Current revision:", current_revision)
    print("Target revision: 39c4e5f6a7b8")

    if current_revision != "f9e8d7c6b5a4":
        raise SystemExit(
            "SAFETY STOP: Revision changed. Recheck migration history."
        )

    confirm = input(
        "\nAfter confirming a backup exists, type "
        "UPGRADE_PRODUCTION to continue: "
    ).strip()

    if confirm != "UPGRADE_PRODUCTION":
        raise SystemExit("Cancelled. No migration was run.")

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    with engine.connect() as connection:
        final_revision = connection.execute(
            text("SELECT version_num FROM public.alembic_version")
        ).scalar_one()

    print("\nFinal revision:", final_revision)

    if final_revision != "39c4e5f6a7b8":
        raise SystemExit(
            "WARNING: Migration did not reach the expected revision."
        )

    print("SUCCESS: Production migration completed.")

finally:
    engine.dispose()
