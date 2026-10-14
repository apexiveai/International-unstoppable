import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import User
import seed_admin


class SeedAdminTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
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
                patch("seed_admin.hash_password", return_value="hashed-password"),
            ):
                seed_admin.seed_admin()

        with Session(self.engine) as db:
            admin = db.scalar(
                select(User).where(User.username == "bootstrap-admin")
            )

        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_super_admin)


if __name__ == "__main__":
    unittest.main()
