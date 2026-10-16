import json
import unittest
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import api
from app.models import Tenant, TrademarkConflictCheck, User


class AdminTrademarkConflictTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(
            self.engine,
            tables=[Tenant.__table__, User.__table__, TrademarkConflictCheck.__table__],
        )
        self.db = Session(self.engine)
        self.tenant = Tenant(name="Neon Works", slug="neon-works")
        self.admin = User(
            username="ops-admin",
            email="ops@example.test",
            password_hash="not-used",
            display_name="Ops Admin",
            tenant_id=None,
            is_active=True,
            is_admin=True,
            is_super_admin=False,
            role="ADMIN",
            account_status="ACTIVE",
        )
        self.client_user = User(
            username="designer",
            email="designer@example.test",
            password_hash="not-used",
            display_name="Kai Designer",
            tenant_id=None,
            is_active=True,
            is_admin=False,
            is_super_admin=False,
            role="USER",
            account_status="ACTIVE",
        )
        self.db.add_all((self.tenant, self.admin, self.client_user))
        self.db.flush()
        self.db.add_all(
            (
                TrademarkConflictCheck(
                    tenant_id=self.tenant.id,
                    user_id=self.client_user.id,
                    original_filename="neon-original.pdf",
                    comparison_filename="neon-competitor.pdf",
                    result_payload=json.dumps({"similarity_percent": 82.5}),
                    created_at=datetime.utcnow(),
                ),
                TrademarkConflictCheck(
                    tenant_id=self.tenant.id,
                    user_id=self.client_user.id,
                    original_filename="other-mark.png",
                    comparison_filename="reference-mark.png",
                    result_payload=json.dumps({"similarity_percent": 14.0}),
                    created_at=datetime.utcnow(),
                ),
            )
        )
        self.db.commit()
        self.original_overrides = dict(api.dependency_overrides)

        def override_db():
            with Session(self.engine) as db:
                yield db

        api.dependency_overrides[get_db] = override_db
        api.dependency_overrides[get_current_user] = lambda: self.admin
        self.http = TestClient(api)

    def tearDown(self):
        self.http.close()
        api.dependency_overrides.clear()
        api.dependency_overrides.update(self.original_overrides)
        self.db.close()
        self.engine.dispose()

    def test_admin_can_search_checks_without_receiving_evidence_payload(self):
        response = self.http.get("/api/admin/trademark-conflicts?q=competitor")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["tenant_name"], "Neon Works")
        self.assertEqual(body["items"][0]["user_email"], "designer@example.test")
        self.assertEqual(body["items"][0]["similarity_percent"], 82.5)
        self.assertNotIn("result", body["items"][0])
        self.assertEqual(body["summary"]["total_checks"], 2)
        self.assertEqual(body["summary"]["workspaces_with_checks"], 1)

    def test_non_admin_cannot_list_checks(self):
        api.dependency_overrides[get_current_user] = lambda: self.client_user

        response = self.http.get("/api/admin/trademark-conflicts")

        self.assertEqual(response.status_code, 403)

    def test_support_role_cannot_list_checks(self):
        self.admin.role = "SUPPORT"

        response = self.http.get("/api/admin/trademark-conflicts")

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()