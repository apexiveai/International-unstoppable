import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import User
import seed_admin


class SeedAdminTests(unittest.TestCase):
    def setUp(self):
        self.database_name = "apexive_community_app"
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        event.listen(
            self.engine,
            "connect",
            lambda connection, _: connection.create_function(
                "current_database", 0, lambda: self.database_name
            ),
        )
        Base.metadata.create_all(self.engine, tables=[User.__table__])
        self.session_factory = sessionmaker(bind=self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_reads_local_env_and_creates_non_super_admin(self):
        env_values = (
            "BOOTSTRAP_ADMIN_USERNAME=bootstrap-admin\n"
            "BOOTSTRAP_ADMIN_EMAIL=admin@example.test\n"
            "BOOTSTRAP_ADMIN_DISPLAY_NAME=Bootstrap Admin\n"
            "BOOTSTRAP_ADMIN_PASSWORD=a-test-password-at-least-16\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(env_values, encoding="utf-8")

            def load_test_env(_path):
                return load_dotenv(env_file)

            with (
                patch.dict(os.environ, {}, clear=True),
                patch("seed_admin.load_dotenv", side_effect=load_test_env),
                patch("seed_admin.SessionLocal", self.session_factory),
                patch(
                    "seed_admin.hash_password", return_value="hashed-password"
                ) as hash_password,
            ):
                seed_admin.seed_admin()
                hash_password.assert_called_once_with(
                    "a-test-password-at-least-16"
                )

        with Session(self.engine) as db:
            admin = db.scalar(
                select(User).where(User.username == "bootstrap-admin")
            )

        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_super_admin)

    def test_refuses_to_create_an_admin_in_another_database(self):
        self.database_name = "another_database"
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "BOOTSTRAP_ADMIN_USERNAME=bootstrap-admin\n"
                "BOOTSTRAP_ADMIN_EMAIL=admin@example.test\n"
                "BOOTSTRAP_ADMIN_DISPLAY_NAME=Bootstrap Admin\n"
                "BOOTSTRAP_ADMIN_PASSWORD=a-test-password-at-least-16\n",
                encoding="utf-8",
            )
            with (
                patch.dict(os.environ, {}, clear=True),
                patch(
                    "seed_admin.load_dotenv",
                    side_effect=lambda _path: load_dotenv(env_file),
                ),
                patch("seed_admin.SessionLocal", self.session_factory),
                patch("seed_admin.hash_password", return_value="hashed-password"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "Refusing to modify database"
                ):
                    seed_admin.seed_admin()

        with Session(self.engine) as db:
            self.assertIsNone(
                db.scalar(select(User).where(User.username == "bootstrap-admin"))
            )

    def test_allows_render_database_and_resets_existing_admin_password(self):
        self.database_name = "apexive_community"
        existing_admin = User(
            username="bootstrap-admin",
            email="admin@example.test",
            password_hash="old-password-hash",
            display_name="Old Admin",
            is_active=True,
            is_admin=True,
            is_super_admin=False,
            role="ADMIN",
            account_status="ACTIVE",
        )
        with Session(self.engine) as db:
            db.add(existing_admin)
            db.commit()

        env_values = (
            "BOOTSTRAP_ADMIN_USERNAME=bootstrap-admin\n"
            "BOOTSTRAP_ADMIN_EMAIL=admin@example.test\n"
            "BOOTSTRAP_ADMIN_DISPLAY_NAME=Bootstrap Admin\n"
            "BOOTSTRAP_ADMIN_PASSWORD=a-test-password-at-least-16\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(env_values, encoding="utf-8")
            with (
                patch.dict(os.environ, {}, clear=True),
                patch(
                    "seed_admin.load_dotenv",
                    side_effect=lambda _path: load_dotenv(env_file),
                ),
                patch("seed_admin.SessionLocal", self.session_factory),
                patch(
                    "seed_admin.hash_password", return_value="new-password-hash"
                ) as hash_password,
            ):
                seed_admin.seed_admin()
                hash_password.assert_called_once_with(
                    "a-test-password-at-least-16"
                )

        with Session(self.engine) as db:
            admin = db.scalar(
                select(User).where(User.username == "bootstrap-admin")
            )

        self.assertIsNotNone(admin)
        self.assertEqual(admin.password_hash, "new-password-hash")
        self.assertEqual(admin.display_name, "Bootstrap Admin")
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_admin)


if __name__ == "__main__":
    unittest.main()
