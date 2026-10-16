import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import api
from app.models import (
    License,
    LicenseActivation,
    LicenseEvent,
    LicensePlan,
    Notification,
    Tenant,
    User,
)


LICENSE_TABLES = [
    Tenant.__table__,
    User.__table__,
    LicensePlan.__table__,
    License.__table__,
    LicenseActivation.__table__,
    LicenseEvent.__table__,
    Notification.__table__,
]


class LicenseManagementTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine, tables=LICENSE_TABLES)
        self.db = Session(self.engine)
        self.tenant = Tenant(name="License customer", slug="license-customer")
        self.db.add(self.tenant)
        self.db.flush()
        self.admin = User(
            username="license-admin",
            email="license-admin@example.test",
            password_hash="unused",
            display_name="License Admin",
            tenant_id=self.tenant.id,
            is_active=True,
            is_admin=True,
            is_super_admin=True,
            role="ADMIN",
            account_status="ACTIVE",
        )
        self.db.add(self.admin)
        self.db.commit()

        self.original_overrides = dict(api.dependency_overrides)

        def override_db():
            with Session(self.engine) as db:
                yield db

        api.dependency_overrides[get_db] = override_db
        api.dependency_overrides[get_current_user] = lambda: self.admin
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        api.dependency_overrides.clear()
        api.dependency_overrides.update(self.original_overrides)
        self.db.close()
        self.engine.dispose()

    def test_generated_license_is_hashed_and_enforces_activation_and_status(self):
        created_plan = self.client.post(
            "/api/admin/licenses/plans",
            json={
                "name": "RPA Standard",
                "description": "Test plan",
                "price": "100.00",
                "currency": "usd",
                "duration_days": 30,
                "max_robots": 1,
                "max_workflows": 2,
                "max_activations": 1,
                "features": {"scheduling": True},
            },
        )
        self.assertEqual(created_plan.status_code, 201, created_plan.text)
        plan_id = created_plan.json()["id"]

        issued = self.client.post(
            "/api/admin/licenses",
            json={"plan_id": plan_id, "tenant_id": self.tenant.id},
        )
        self.assertEqual(issued.status_code, 201, issued.text)
        license_key = issued.json()["license_key"]
        license_id = issued.json()["license"]["id"]
        stored = self.db.get(License, license_id)
        self.assertEqual(stored.key_hash, hashlib.sha256(license_key.encode()).hexdigest())
        self.assertNotIn(license_key, stored.key_hash)
        self.assertNotIn("key_hash", issued.json()["license"])

        headers = {"X-RPA-Service-Token": "service-secret"}
        with patch("app.api.licenses.settings.rpa_license_service_token", "service-secret"):
            valid = self.client.post(
                "/api/licenses/validate",
                headers=headers,
                json={
                    "license_key": license_key,
                    "device_id": "robot-1",
                    "device_name": "Robot 1",
                    "workflow_count": 2,
                },
            )
            self.assertEqual(valid.status_code, 200, valid.text)
            self.assertTrue(valid.json()["valid"])
            activation_limited = self.client.post(
                "/api/licenses/validate",
                headers=headers,
                json={"license_key": license_key, "device_id": "robot-2"},
            )
            self.assertEqual(activation_limited.status_code, 403)
            workflow_limited = self.client.post(
                "/api/licenses/validate",
                headers=headers,
                json={"license_key": license_key, "workflow_count": 3},
            )
            self.assertEqual(workflow_limited.status_code, 403)

        activations = self.client.get("/api/admin/licenses").json()["items"][0]["activations"]
        deactivated = self.client.post(
            f"/api/admin/licenses/activations/{activations[0]['id']}/deactivate"
        )
        self.assertEqual(deactivated.status_code, 200)

        with patch("app.api.licenses.settings.rpa_license_service_token", "service-secret"):
            second_robot = self.client.post(
                "/api/licenses/validate",
                headers=headers,
                json={"license_key": license_key, "device_id": "robot-2"},
            )
            self.assertEqual(second_robot.status_code, 200, second_robot.text)

        suspended = self.client.post(
            f"/api/admin/licenses/{license_id}/status",
            json={"status": "suspended"},
        )
        self.assertEqual(suspended.status_code, 200)
        with patch("app.api.licenses.settings.rpa_license_service_token", "service-secret"):
            blocked = self.client.post(
                "/api/licenses/validate",
                headers=headers,
                json={"license_key": license_key},
            )
            self.assertEqual(blocked.status_code, 403)

        events = self.client.get("/api/admin/licenses").json()["items"][0]["events"]
        self.assertIn("issued", [event["event_type"] for event in events])
        self.assertIn("activated", [event["event_type"] for event in events])
        self.assertIn("suspended", [event["event_type"] for event in events])

    def test_renewal_alerts_create_customer_notifications_once(self):
        client_user = User(
            username="license-customer",
            email="license-customer@example.test",
            password_hash="unused",
            display_name="License Customer",
            tenant_id=self.tenant.id,
            is_active=True,
            is_admin=False,
            is_super_admin=False,
            role="USER",
            account_status="ACTIVE",
        )
        plan = LicensePlan(
            name="Renewing RPA Plan",
            description="",
            price=100,
            currency="USD",
            duration_days=30,
            max_robots=2,
            max_workflows=5,
            max_activations=2,
            features={},
            is_active=True,
        )
        self.db.add_all((client_user, plan))
        self.db.flush()
        license = License(
            key_hash=hashlib.sha256(b"unused-test-key").hexdigest(),
            tenant_id=self.tenant.id,
            plan_id=plan.id,
            status="active",
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=5),
            price=plan.price,
            currency=plan.currency,
            created_by_id=self.admin.id,
        )
        self.db.add(license)
        self.db.commit()

        first = self.client.post("/api/admin/licenses/renewals/send")
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["notifications_created"], 1)
        self.assertEqual(first.json()["email_attempts"], 0)

        second = self.client.post("/api/admin/licenses/renewals/send")
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(second.json()["notifications_created"], 0)
        self.assertEqual(
            self.db.query(Notification)
            .filter_by(recipient_id=client_user.id, entity_id=license.id)
            .count(),
            1,
        )
