import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

from app.database import SessionLocal
from app.auth import hash_password
from app.models import User


def seed_admin() -> None:
    load_dotenv(Path(__file__).resolve().with_name(".env"))

    username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "").strip()
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    display_name = os.environ.get("BOOTSTRAP_ADMIN_DISPLAY_NAME", "").strip()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    if not all((username, email, display_name, password)):
        raise RuntimeError(
            "Set BOOTSTRAP_ADMIN_USERNAME, BOOTSTRAP_ADMIN_EMAIL, "
            "BOOTSTRAP_ADMIN_DISPLAY_NAME, and BOOTSTRAP_ADMIN_PASSWORD "
            "through a secure secret mechanism."
        )
    if len(password) < 16:
        raise RuntimeError("The bootstrap administrator password must be at least 16 characters.")

    db = SessionLocal()
    try:
        existing = db.scalar(
            select(User).where((User.username == username) | (User.email == email))
        )
        if existing is not None:
            if existing.username != username or existing.email.lower() != email:
                raise RuntimeError("The configured username or email is already in use.")
            if not existing.is_admin or not existing.is_active:
                raise RuntimeError(
                    "The existing account is not an active administrator; no account changes were made."
                )
            print("The configured active administrator already exists; no changes were made.")
            return

        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            is_active=True,
            is_admin=True,
            is_super_admin=False,
        )
        db.add(admin)
        db.commit()
        print("Initial administrator created. No Super Admin role was assigned.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
