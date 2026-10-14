import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import api
from app.models import (
    Payment,
    ProductAccessGrant,
    ProductLaunchCode,
    Subscription,
    SubscriptionPlan,
    SystemAuditEvent,
    Tenant,
    TenantAuditLog,
    User,
)
from fastapi import HTTPException

from app.services.product_access import (
    require_tenant_product_access,
    subscription_is_active,
    tenant_product_access,
)


TEST_TABLES = [
    Tenant.__table__,
    User.__table__,
    SubscriptionPlan.__table__,
    Subscription.__table__,
    Payment.__table__,
    ProductAccessGrant.__table__,
    ProductLaunchCode.__table__,
    TenantAuditLog.__table__,
    SystemAuditEvent.__table__,
]


class SubscriptionEntitlementTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine, tables=TEST_TABLES)
        self.db = Session(self.engine)
        self.tenant_a = Tenant(name="Tenant A", slug="tenant-a")
        self.tenant_b = Tenant(name="Tenant B", slug="tenant-b")
        self.db.add_all((self.tenant_a, self.tenant_b))
        self.db.flush()
        self.user = User(
            username="customer-a",
            email="customer-a@example.test",
            password_hash="not-used",
            display_name="Customer A",
            tenant_id=self.tenant_a.id,
            is_active=True,
            is_admin=False,
            is_super_admin=False,
        )
        self.regular_admin = User(
            username="ordinary-admin",
            email="ordinary-admin@example.test",
            password_hash="not-used",
            display_name="Ordinary Admin",
            tenant_id=self.tenant_a.id,
            is_active=True,
            is_admin=True,
            is_super_admin=False,
        )
        self.super_admin = User(
            username="root-admin",
            email="root-admin@example.test",
            password_hash="not-used",
            display_name="Root Admin",
            tenant_id=self.tenant_a.id,
            is_active=True,
            is_admin=True,
            is_super_admin=True,
        )
        self.db.add_all((self.user, self.regular_admin, self.super_admin))
        self.plan = SubscriptionPlan(
            product_key="trademark",
            name="Trademark",
            description="Test plan",
            monthly_price=Decimal("10.00"),
            currency="USD",
            billing_cycle="monthly",
            is_active=True,
        )
        self.db.add(self.plan)
        self.db.commit()

        self.original_overrides = dict(api.dependency_overrides)

        def override_db():
            with Session(self.engine) as db:
                yield db

        api.dependency_overrides[get_db] = override_db
        api.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        api.dependency_overrides.clear()
        api.dependency_overrides.update(self.original_overrides)
        self.db.close()
        self.engine.dispose()

    def add_subscription(self, *, status="active", end_delta=timedelta(days=1), tenant=None):
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            tenant_id=(tenant or self.tenant_a).id,
            plan_id=self.plan.id,
            status=status,
            price=Decimal("10.00"),
            currency="USD",
            billing_cycle="monthly",
            start_date=now - timedelta(days=1),
            current_period_end=now + end_delta if end_delta is not None else None,
        )
        self.db.add(subscription)
        self.db.flush()
        return subscription

    def add_payment(self, subscription, status="verified", tenant=None):
        payment = Payment(
            tenant_id=(tenant or self.tenant_a).id,
            plan_id=self.plan.id,
            subscription_id=subscription.id,
            provider="manual_review",
            payment_method="card",
            status=status,
            amount=Decimal("10.00"),
            currency="USD",
            checkout_reference=f"test-{subscription.id}-{status}",
        )
        self.db.add(payment)
        self.db.flush()
        return payment

    def add_grant(
        self,
        *,
        tenant=None,
        starts_delta=timedelta(days=-1),
        ends_delta=timedelta(days=1),
        revoked=False,
    ):
        now = datetime.now(timezone.utc)
        grant = ProductAccessGrant(
            tenant_id=(tenant or self.tenant_a).id,
            product_key="trademark",
            access_type="complimentary",
            starts_at=now + starts_delta,
            expires_at=now + ends_delta if ends_delta is not None else None,
            is_permanent=ends_delta is None,
            reason="Test grant",
            granted_by_id=self.super_admin.id,
            revoked_at=now if revoked else None,
            revoked_by_id=self.super_admin.id if revoked else None,
        )
        self.db.add(grant)
        self.db.flush()
        return grant

    def test_no_entitlement_is_denied(self):
        access = tenant_product_access(self.db, self.tenant_a.id, "trademark")
        self.assertFalse(access["has_access"])
        with self.assertRaises(HTTPException) as denied:
            require_tenant_product_access(self.db, self.tenant_a.id, "trademark")
        self.assertEqual(denied.exception.status_code, 403)

    def test_verified_active_payment_grants_only_matching_tenant_product(self):
        subscription = self.add_subscription()
        self.add_payment(subscription)
        self.db.commit()

        access = tenant_product_access(self.db, self.tenant_a.id, "trademark")
        self.assertTrue(access["has_access"])
        self.assertEqual(access["source"], "subscription")
        self.assertFalse(
            tenant_product_access(self.db, self.tenant_b.id, "trademark")["has_access"]
        )
        self.assertFalse(
            tenant_product_access(self.db, self.tenant_a.id, "workforce")["has_access"]
        )

    def test_pending_and_failed_payments_do_not_grant_access(self):
        for payment_status in ("pending", "failed"):
            subscription = self.add_subscription()
            self.add_payment(subscription, status=payment_status)
        self.db.commit()
        self.assertFalse(
            tenant_product_access(self.db, self.tenant_a.id, "trademark")["has_access"]
        )

    def test_expired_or_future_subscription_is_inactive(self):
        expired = Subscription(
            status="active",
            current_period_end=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        future = Subscription(
            status="active",
            start_date=datetime.now(timezone.utc) + timedelta(days=1),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=2),
        )
        self.assertFalse(subscription_is_active(expired))
        self.assertFalse(subscription_is_active(future))

    def test_valid_complimentary_grant_grants_access(self):
        self.add_grant()
        self.db.commit()
        access = tenant_product_access(self.db, self.tenant_a.id, "trademark")
        self.assertTrue(access["has_access"])
        self.assertEqual(access["source"], "enterprise_grant")

    def test_expired_revoked_and_not_yet_started_grants_are_denied(self):
        self.add_grant(ends_delta=timedelta(seconds=-1))
        self.add_grant(revoked=True)
        self.add_grant(starts_delta=timedelta(days=2))
        self.db.commit()
        self.assertFalse(
            tenant_product_access(self.db, self.tenant_a.id, "trademark")["has_access"]
        )

    def test_unpublished_products_cannot_be_used_for_subscription_access(self):
        self.assertFalse(
            tenant_product_access(self.db, self.tenant_a.id, "mna")["has_access"]
        )

    def test_product_api_requires_entitlement(self):
        self.db.commit()
        response = self.client.get("/api/subscriptions/access/trademark")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["has_access"])

    def test_detector_rejects_unauthenticated_requests(self):
        api.dependency_overrides.pop(get_current_user, None)
        response = self.client.post("/api/clone-detector/analyze")
        self.assertEqual(response.status_code, 401)

    def test_detector_denies_before_processing_or_parsing_uploads(self):
        with patch("app.api.clone_detector.analyze_clone") as analyze:
            response = self.client.post(
                "/api/clone-detector/analyze",
                files={
                    "original": ("original.pdf", b"%PDF-1.4", "application/pdf"),
                    "comparison": ("comparison.pdf", b"%PDF-1.4", "application/pdf"),
                },
            )
        self.assertEqual(response.status_code, 403)
        analyze.assert_not_called()

    def test_detector_accepts_entitled_upload_and_associates_trusted_user(self):
        self.add_grant()
        self.db.commit()
        result = {
            "overall_similarity": 0.0,
            "similarity_percent": 0.0,
            "matching_area_count": 0,
            "matched_points": 0,
            "matches": [],
            "annotated_original": [],
            "original_page_count": 0,
            "comparison_page_count": 0,
            "engine": {},
        }
        with patch("app.api.clone_detector.analyze_clone", return_value=result) as analyze:
            response = self.client.post(
                "/api/clone-detector/analyze",
                files={
                    "original": ("original.pdf", b"%PDF-1.4", "application/pdf"),
                    "comparison": ("comparison.pdf", b"%PDF-1.4", "application/pdf"),
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(analyze.call_args.kwargs["original_bytes"], b"%PDF-1.4")

    def test_detector_rejects_invalid_file_signatures(self):
        self.add_grant()
        self.db.commit()
        with patch("app.api.clone_detector.analyze_clone") as analyze:
            response = self.client.post(
                "/api/clone-detector/analyze",
                files={
                    "original": ("original.pdf", b"not a PDF", "application/pdf"),
                    "comparison": ("comparison.pdf", b"%PDF-1.4", "application/pdf"),
                },
            )
        self.assertEqual(response.status_code, 400)
        analyze.assert_not_called()

    def test_regular_administrator_cannot_use_platform_admin_routes(self):
        api.dependency_overrides[get_current_user] = lambda: User(
            id=987,
            is_active=True,
            is_admin=True,
            is_super_admin=False,
        )
        response = self.client.get("/api/admin/accounts")
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_cancel_subscription(self):
        subscription = self.add_subscription()
        self.db.commit()

        response = self.client.post(
            f"/api/subscriptions/{subscription.id}/cancel"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.db.get(Subscription, subscription.id).status, "active")

    def test_ordinary_admin_can_cancel_any_subscription(self):
        subscription = self.add_subscription(tenant=self.tenant_b)
        self.db.commit()
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        response = self.client.post(
            f"/api/admin/subscriptions/{subscription.id}/cancel"
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "cancelled")

    def test_customer_can_submit_payment_request_for_admin_review(self):
        response = self.client.post(
            "/api/payments/create",
            json={"plan_id": self.plan.id, "payment_method": "card"},
        )

        self.assertEqual(response.status_code, 201, response.text)
        payment = response.json()
        self.assertEqual(payment["status"], "pending")
        self.assertIsNotNone(payment["subscription_id"])
        subscription = self.db.get(Subscription, payment["subscription_id"])
        self.assertEqual(subscription.status, "pending")
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        verified = self.client.post(f"/api/admin/payments/{payment['id']}/verify")
        activated = self.client.post(
            f"/api/admin/subscriptions/{subscription.id}/activate",
            json={"duration_days": 30},
        )

        self.assertEqual(verified.status_code, 200, verified.text)
        self.assertEqual(activated.status_code, 200, activated.text)
        self.db.expire_all()
        self.assertTrue(
            tenant_product_access(self.db, self.tenant_a.id, "trademark")[
                "has_access"
            ]
        )

    def test_ordinary_admin_can_create_a_manual_subscription(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        response = self.client.post(
            "/api/admin/subscriptions",
            json={
                "tenant_id": self.tenant_b.id,
                "plan_id": self.plan.id,
                "duration_days": 45,
                "reason": "Approved enterprise subscription",
            },
        )

        self.assertEqual(response.status_code, 201, response.text)
        created = response.json()
        self.assertEqual(created["tenant_id"], self.tenant_b.id)
        self.assertEqual(created["status"], "active")
        self.assertEqual(created["price"], "10.00")
        self.db.expire_all()
        self.assertTrue(
            tenant_product_access(self.db, self.tenant_b.id, "trademark")[
                "has_access"
            ]
        )
        audit = self.db.query(TenantAuditLog).filter_by(
            action="subscription.admin_created"
        ).one()
        self.assertEqual(audit.actor_user_id, self.regular_admin.id)

    def test_customer_cannot_create_a_manual_subscription(self):
        response = self.client.post(
            "/api/admin/subscriptions",
            json={
                "tenant_id": self.tenant_a.id,
                "plan_id": self.plan.id,
                "duration_days": 30,
                "reason": "Approved subscription",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_ordinary_admin_cannot_override_payment_verification(self):
        subscription = self.add_subscription(status="pending")
        self.db.commit()
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        response = self.client.post(
            f"/api/admin/subscriptions/{subscription.id}/activate",
            json={
                "override_verified_payment": True,
                "override_reason": "No payment received",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.db.get(Subscription, subscription.id).status, "pending")

    def test_ordinary_admin_can_renew_expired_subscription(self):
        subscription = self.add_subscription(
            status="expired", end_delta=timedelta(days=-10)
        )
        previous_end = subscription.current_period_end
        self.db.commit()
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin
        expected_end = max(
            datetime.now(timezone.utc).replace(tzinfo=None),
            previous_end.replace(tzinfo=None),
        ) + timedelta(days=30)

        response = self.client.post(
            f"/api/admin/subscriptions/{subscription.id}/renew",
            json={
                "duration_days": 30,
                "reason": "Renewal approved",
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        renewed = response.json()
        self.assertEqual(renewed["status"], "active")
        actual_end = datetime.fromisoformat(renewed["current_period_end"])
        self.assertLess(
            abs((actual_end - expected_end).total_seconds()),
            5,
        )
        self.db.expire_all()
        self.assertTrue(
            tenant_product_access(self.db, self.tenant_a.id, "trademark")[
                "has_access"
            ]
        )
        audit = self.db.query(TenantAuditLog).filter_by(
            action="subscription.renewed"
        ).one()
        self.assertEqual(audit.actor_user_id, self.regular_admin.id)

    def test_ordinary_admin_can_list_subscription_clients(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        response = self.client.get("/api/admin/subscription-clients")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["items"][0]["id"], self.user.id)

    def test_super_administrator_can_use_platform_admin_routes(self):
        api.dependency_overrides[get_current_user] = lambda: self.super_admin
        response = self.client.get("/api/admin/accounts")
        self.assertEqual(response.status_code, 200)

    def test_launch_code_is_hash_only_and_one_time(self):
        self.add_grant()
        raw_code = "secure-one-time-test-code-0123456789"
        code_hash = hashlib.sha256(raw_code.encode("utf8")).hexdigest()
        self.db.add(
            ProductLaunchCode(
                code_hash=code_hash,
                user_id=self.user.id,
                tenant_id=self.tenant_a.id,
                product_key="trademark",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
            )
        )
        self.db.commit()

        first = self.client.post(
            "/api/subscriptions/launch/exchange",
            json={"code": raw_code},
        )
        second = self.client.post(
            "/api/subscriptions/launch/exchange",
            json={"code": raw_code},
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["product_key"], "trademark")
        self.assertEqual(second.status_code, 401)
        stored = self.db.get(ProductLaunchCode, code_hash)
        self.assertIsNotNone(stored.consumed_at)

    def test_expired_and_wrong_tenant_launch_codes_are_rejected(self):
        self.add_grant()
        expired_code = "expired-code-for-test-0123456789abcdef"
        wrong_tenant_code = "wrong-tenant-code-for-test-0123456789abcdef"
        self.db.add_all(
            (
                ProductLaunchCode(
                    code_hash=hashlib.sha256(expired_code.encode()).hexdigest(),
                    user_id=self.user.id,
                    tenant_id=self.tenant_a.id,
                    product_key="trademark",
                    expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
                ),
                ProductLaunchCode(
                    code_hash=hashlib.sha256(wrong_tenant_code.encode()).hexdigest(),
                    user_id=self.user.id,
                    tenant_id=self.tenant_b.id,
                    product_key="trademark",
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
                ),
            )
        )
        self.db.commit()

        expired = self.client.post(
            "/api/subscriptions/launch/exchange",
            json={"code": expired_code},
        )
        wrong_tenant = self.client.post(
            "/api/subscriptions/launch/exchange",
            json={"code": wrong_tenant_code},
        )
        self.assertEqual(expired.status_code, 401)
        self.assertEqual(wrong_tenant.status_code, 403)

    def test_launch_code_conditional_update_prevents_replay(self):
        raw_code = "atomic-code-test-0123456789abcdef"
        code_hash = hashlib.sha256(raw_code.encode()).hexdigest()
        self.db.add(
            ProductLaunchCode(
                code_hash=code_hash,
                user_id=self.user.id,
                tenant_id=self.tenant_a.id,
                product_key="trademark",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
            )
        )
        self.db.commit()
        now = datetime.now(timezone.utc)
        first = self.db.execute(
            update(ProductLaunchCode)
            .where(
                ProductLaunchCode.code_hash == code_hash,
                ProductLaunchCode.consumed_at.is_(None),
                ProductLaunchCode.revoked_at.is_(None),
                ProductLaunchCode.expires_at > now,
            )
            .values(consumed_at=now)
        )
        second = self.db.execute(
            update(ProductLaunchCode)
            .where(
                ProductLaunchCode.code_hash == code_hash,
                ProductLaunchCode.consumed_at.is_(None),
                ProductLaunchCode.revoked_at.is_(None),
                ProductLaunchCode.expires_at > now,
            )
            .values(consumed_at=now)
        )
        self.assertEqual(first.rowcount, 1)
        self.assertEqual(second.rowcount, 0)
