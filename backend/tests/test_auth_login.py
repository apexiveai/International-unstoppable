from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.auth import login
from app.auth import hash_password
from app.database import Base
from app.models import User


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine, tables=[User.__table__])
        self.db = Session(self.engine)
        self.db.add(
            User(
                username="bootstrap-admin",
                email="admin@example.test",
                password_hash=hash_password("a-test-password-at-least-16"),
                display_name="Bootstrap Admin",
                is_active=True,
                is_admin=True,
                account_status="ACTIVE",
            )
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_accepts_email_case_insensitively(self):
        form_data = SimpleNamespace(
            username="  ADMIN@EXAMPLE.TEST  ",
            password="a-test-password-at-least-16",
        )

        with patch("app.api.auth.create_access_token", return_value="test-token"):
            response = login(form_data=form_data, db=self.db)

        self.assertEqual(response["access_token"], "test-token")
        self.assertEqual(response["user"].username, "bootstrap-admin")
