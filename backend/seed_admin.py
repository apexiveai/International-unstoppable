from datetime import datetime, timezone
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

from app.database import SessionLocal
from app.auth import hash_password
from app.models import User

BOOTSTRAP_DATABASE_NAMES = {
    "apexive_community_app",
    "apexive_admin_eisn",
}


def seed_admin() -> None:
    load_dotenv(Path(__file__).resolve().with_name(".env"))

    username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "").strip()
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    display_name = os.environ.get("BOOTSTRAP_ADMIN_DISPLAY_NAME", "").strip()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")

    if not all((username, email, display_name, password)):
        raise RuntimeError(
            "Set BOOTSTRAP_ADMIN_USERNAME, BOOTSTRAP_ADMIN_EMAIL, "
            "BOOTSTRAP_ADMIN_DISPLAY_NAME, and BOOTSTRAP_ADMIN_PASSWORD."
        )

    if len(password) < 16:
        raise RuntimeError(
            "The bootstrap administrator password must be at least 16 characters."
        )
    db = SessionLocal()
    try:
        from sqlalchemy import text

        database_name = db.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if database_name not in BOOTSTRAP_DATABASE_NAMES:
            raise RuntimeError(
                "Refusing to modify database "
                f"{database_name!r}; expected one of "
                f"{', '.join(sorted(BOOTSTRAP_DATABASE_NAMES))}."
            )

        existing = db.scalar(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )

        now = datetime.now(timezone.utc)

        if existing is not None:
            if existing.username != username or existing.email.lower() != email:
                raise RuntimeError(
                    "Configured username/email conflicts with an existing account."
                )
            if not existing.is_admin or existing.is_super_admin:
                raise RuntimeError(
                    "The configured account is not an ordinary administrator; "
                    "no account changes were made."
                )

            existing.password_hash = hash_password(password)
            existing.display_name = display_name
            existing.is_active = True
            existing.is_admin = True
            existing.is_super_admin = False
            existing.role = "ADMIN"
            existing.account_status = "ACTIVE"

            if existing.approved_at is None:
                existing.approved_at = now

            db.commit()
            print("Existing ordinary administrator updated successfully.")
            print(f"Username: {existing.username}")
            print("Password: reset from BOOTSTRAP_ADMIN_PASSWORD.")
            return

        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            is_active=True,
            is_admin=True,
            is_super_admin=False,
            role="ADMIN",
            account_status="ACTIVE",
            approved_at=now,
        )

        db.add(admin)
        db.commit()

        print("Ordinary administrator account created successfully.")
        print(f"Username: {admin.username}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()