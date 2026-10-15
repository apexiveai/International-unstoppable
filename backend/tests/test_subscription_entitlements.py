import asyncio
import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit
from unittest.mock import AsyncMock, Mock

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
    TrademarkConflictCheck,
    User,
)
from app.schemas.clone_detector import CloneDetectorResponse
from fastapi import HTTPException

from app.services.product_access import (
    add_months,
    require_tenant_product_access,
    subscription_is_active,
    tenant_product_access,
)
from app.services.spaceship_domains import check_domain_availability


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
    TrademarkConflictCheck.__table__,
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
            account_status="ACTIVE",
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
            role="ADMIN",
            account_status="ACTIVE",
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
            code="TRADEMARK_CONFLICT",
            product_key="trademark",
            name="Trademark",
            description="Test plan",
            monthly_price=Decimal("7000000.00"),
            currency="MMK",
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

    def test_trademark_complimentary_grant_does_not_bypass_payment_requirement(self):
        self.add_grant()
        self.db.commit()
        access = tenant_product_access(self.db, self.tenant_a.id, "trademark")
        self.assertFalse(access["has_access"])
        self.assertIsNone(access["source"])

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

    def test_administrator_has_access_to_all_published_products(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        trademark_access = self.client.get("/api/subscriptions/access/trademark")
        workforce_access = self.client.get("/api/subscriptions/access/workforce")
        launch = self.client.post("/api/subscriptions/products/trademark/launch")

        self.assertEqual(trademark_access.status_code, 200, trademark_access.text)
        self.assertTrue(trademark_access.json()["has_access"])
        self.assertEqual(trademark_access.json()["status"], "active")
        self.assertEqual(workforce_access.status_code, 200, workforce_access.text)
        self.assertTrue(workforce_access.json()["has_access"])
        self.assertEqual(launch.status_code, 200, launch.text)

        access_code = parse_qs(urlsplit(launch.json()["url"]).query)["access_code"][0]
        exchange = self.client.post(
            "/api/subscriptions/launch/exchange",
            json={"code": access_code},
        )
        self.assertEqual(exchange.status_code, 200, exchange.text)

    def test_administrator_can_use_trademark_without_a_subscription(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin
        result = CloneDetectorResponse(
            overall_similarity=0.0,
            similarity_percent=0.0,
            matching_area_count=0,
            matched_points=0,
            matches=[],
            annotated_original=[],
            original_page_count=0,
            comparison_page_count=0,
            engine={},
        )

        with patch("app.api.clone_detector.analyze_clone", return_value=result) as analyze:
            response = self.client.post(
                "/api/clone-detector/analyze",
                files={
                    "original": ("original.pdf", b"%PDF-1.4", "application/pdf"),
                    "comparison": ("comparison.pdf", b"%PDF-1.4", "application/pdf"),
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        analyze.assert_called_once()
        self.assertEqual(
            self.client.get("/api/clone-detector/checks").status_code,
            200,
        )

    def test_support_role_does_not_bypass_product_entitlement(self):
        support = User(
            id=987,
            tenant_id=self.tenant_a.id,
            is_active=True,
            is_admin=True,
            role="SUPPORT",
            account_status="ACTIVE",
        )
        api.dependency_overrides[get_current_user] = lambda: support

        access = self.client.get("/api/subscriptions/access/trademark")
        detector = self.client.get("/api/clone-detector/checks")

        self.assertEqual(access.status_code, 200)
        self.assertFalse(access.json()["has_access"])
        self.assertEqual(detector.status_code, 403)

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

    def test_spaceship_domain_lookup_requires_trademark_entitlement(self):
        with patch(
            "app.api.clone_detector.check_domain_availability",
            new_callable=AsyncMock,
        ) as lookup:
            response = self.client.post(
                "/api/clone-detector/domains/availability",
                json={"domain": "example.com"},
            )

        self.assertEqual(response.status_code, 403)
        lookup.assert_not_awaited()

    def test_spaceship_domain_lookup_returns_availability_for_entitled_tenant(self):
        subscription = self.add_subscription()
        self.add_payment(subscription)
        self.db.commit()

        with patch(
            "app.api.clone_detector.check_domain_availability",
            new_callable=AsyncMock,
            return_value={"domain": "example.com", "result": "available"},
        ) as lookup:
            response = self.client.post(
                "/api/clone-detector/domains/availability",
                json={"domain": " Example.COM. "},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.json(),
            {"domain": "example.com", "result": "available"},
        )
        lookup.assert_awaited_once_with("example.com")

    def test_spaceship_domain_lookup_rejects_urls(self):
        response = self.client.post(
            "/api/clone-detector/domains/availability",
            json={"domain": "https://example.com"},
        )

        self.assertEqual(response.status_code, 422)

    def test_spaceship_service_posts_to_availability_api(self):
        response = Mock(status_code=200, is_success=True)
        response.json.return_value = {
            "domains": [{"domain": "example.com", "result": "available"}]
        }
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.post.return_value = response

        with (
            patch("app.services.spaceship_domains.settings.spaceship_api_key", "key"),
            patch(
                "app.services.spaceship_domains.settings.spaceship_api_secret",
                "secret",
            ),
            patch(
                "app.services.spaceship_domains.httpx.AsyncClient",
                return_value=client,
            ),
        ):
            result = asyncio.run(check_domain_availability("example.com"))

        self.assertEqual(result, {"domain": "example.com", "result": "available"})
        client.post.assert_awaited_once_with(
            "https://spaceship.dev/api/v1/domains/available",
            headers={
                "X-Api-Key": "key",
                "X-Api-Secret": "secret",
                "Content-Type": "application/json",
            },
            json={"domains": ["example.com"]},
        )

    def test_detector_accepts_entitled_upload_and_associates_trusted_user(self):
        subscription = self.add_subscription()
        self.add_payment(subscription)
        self.db.commit()
        result = CloneDetectorResponse(
            overall_similarity=0.0,
            similarity_percent=0.0,
            matching_area_count=0,
            matched_points=0,
            matches=[],
            annotated_original=[],
            original_page_count=0,
            comparison_page_count=0,
            engine={},
        )
        with patch("app.api.clone_detector.analyze_clone", return_value=result) as analyze:
            response = self.client.post(
                "/api/clone-detector/analyze",
                files={
                    "original": ("original.pdf", b"%PDF-1.4", "application/pdf"),
                    "comparison": ("comparison.pdf", b"%PDF-1.4", "application/pdf"),
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(analyze.call_args.kwargs["original_bytes"], b"%PDF-1.4")
        check = self.db.query(TrademarkConflictCheck).one()
        self.assertEqual(check.tenant_id, self.tenant_a.id)
        self.assertEqual(check.user_id, self.user.id)

    def test_detector_rejects_invalid_file_signatures(self):
        subscription = self.add_subscription()
        self.add_payment(subscription)
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

    def test_ordinary_admin_can_approve_pending_account_in_another_tenant(self):
        pending_user = User(
            username="customer-b-pending",
            email="customer-b-pending@example.test",
            password_hash="not-used",
            display_name="Customer B Pending",
            tenant_id=self.tenant_b.id,
            is_active=False,
            is_admin=False,
            role="USER",
            account_status="PENDING",
        )
        self.db.add(pending_user)
        self.db.commit()
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        pending_users = self.client.get("/api/admin/users/pending")
        self.assertEqual(pending_users.status_code, 200, pending_users.text)
        self.assertIn(pending_user.id, [user["id"] for user in pending_users.json()])

        response = self.client.post(f"/api/admin/users/{pending_user.id}/approve")

        self.assertEqual(response.status_code, 200, response.text)
        self.db.refresh(pending_user)
        self.assertEqual(pending_user.account_status, "ACTIVE")
        self.assertTrue(pending_user.is_active)
        self.assertEqual(pending_user.approved_by, self.regular_admin.id)

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

    def test_admin_confirmation_activates_subscription_and_grants_access(self):
        response = self.client.post(
            "/api/payments/create",
            json={
                "plan_id": self.plan.id,
                "payment_method": "card",
                "accepted_contract": True,
            },
        )

        self.assertEqual(response.status_code, 201, response.text)
        payment = response.json()
        self.assertEqual(payment["status"], "pending")
        self.assertEqual(payment["amount"], "7000000.00")
        self.assertEqual(payment["currency"], "MMK")
        self.assertIsNotNone(payment["subscription_id"])
        subscription = self.db.get(Subscription, payment["subscription_id"])
        self.assertEqual(subscription.status, "pending")
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        verified = self.client.post(f"/api/admin/payments/{payment['id']}/verify")

        self.assertEqual(verified.status_code, 200, verified.text)
        self.db.expire_all()
        self.assertEqual(self.db.get(Subscription, subscription.id).status, "active")
        self.assertEqual(
            self.db.get(Payment, payment["id"]).status,
            "verified",
        )
        activated = self.db.get(Subscription, subscription.id)
        self.assertEqual(activated.contract_months, 8)
        self.assertEqual(
            activated.contract_end,
            add_months(activated.start_date, 8),
        )
        self.assertTrue(
            tenant_product_access(self.db, self.tenant_a.id, "trademark")[
                "has_access"
            ]
        )

    def test_trademark_request_requires_explicit_contract_acceptance(self):
        response = self.client.post(
            "/api/payments/create",
            json={"plan_id": self.plan.id, "payment_method": "card"},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.db.query(Subscription).count(), 0)

    def test_monthly_installment_extends_the_same_eight_month_contract(self):
        first_payment = self.client.post(
            "/api/payments/create",
            json={
                "plan_id": self.plan.id,
                "payment_method": "card",
                "accepted_contract": True,
            },
        )
        self.assertEqual(first_payment.status_code, 201, first_payment.text)
        subscription_id = first_payment.json()["subscription_id"]
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin
        first_verification = self.client.post(
            f"/api/admin/payments/{first_payment.json()['id']}/verify"
        )
        self.assertEqual(first_verification.status_code, 200, first_verification.text)
        subscription = self.db.get(Subscription, subscription_id)
        contract_end = subscription.contract_end
        subscription.current_period_end = datetime.now(timezone.utc).replace(
            tzinfo=None
        ) - timedelta(seconds=1)
        self.db.commit()

        api.dependency_overrides[get_current_user] = lambda: self.user
        next_payment = self.client.post(
            "/api/payments/create",
            json={"plan_id": self.plan.id, "payment_method": "card"},
        )
        self.assertEqual(next_payment.status_code, 201, next_payment.text)
        self.assertEqual(next_payment.json()["subscription_id"], subscription_id)
        self.assertEqual(next_payment.json()["amount"], "7000000.00")
        self.assertEqual(next_payment.json()["currency"], "MMK")

        api.dependency_overrides[get_current_user] = lambda: self.regular_admin
        next_verification = self.client.post(
            f"/api/admin/payments/{next_payment.json()['id']}/verify"
        )
        self.assertEqual(next_verification.status_code, 200, next_verification.text)
        self.db.expire_all()
        renewed = self.db.get(Subscription, subscription_id)
        self.assertEqual(renewed.contract_months, 8)
        self.assertEqual(renewed.contract_end, contract_end)
        self.assertGreater(renewed.current_period_end, datetime.now(timezone.utc).replace(tzinfo=None))

    def test_trademark_history_is_tenant_scoped(self):
        subscription = self.add_subscription()
        self.add_payment(subscription)
        own_check = TrademarkConflictCheck(
            tenant_id=self.tenant_a.id,
            user_id=self.user.id,
            original_filename="company-a.pdf",
            comparison_filename="comparison.pdf",
            result_payload='{"similarity_percent": 42.0}',
        )
        other_check = TrademarkConflictCheck(
            tenant_id=self.tenant_b.id,
            user_id=self.user.id,
            original_filename="company-b.pdf",
            comparison_filename="comparison.pdf",
            result_payload='{"similarity_percent": 74.0}',
        )
        self.db.add_all((own_check, other_check))
        self.db.commit()

        history = self.client.get("/api/clone-detector/checks")
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(
            [item["original_filename"] for item in history.json()["items"]],
            ["company-a.pdf"],
        )
        hidden = self.client.get(
            f"/api/clone-detector/checks/{other_check.id}"
        )
        self.assertEqual(hidden.status_code, 404)

    def test_successful_analysis_is_saved_with_visual_result(self):
        subscription = self.add_subscription()
        self.add_payment(subscription)
        self.db.commit()
        result = CloneDetectorResponse(
            overall_similarity=0.5,
            similarity_percent=50.0,
            matching_area_count=1,
            matched_points=12,
            matches=[],
            annotated_original=[],
            original_page_count=1,
            comparison_page_count=1,
            engine={"name": "test"},
        )
        with patch(
            "app.api.clone_detector.analyze_clone",
            return_value=result,
        ):
            response = self.client.post(
                "/api/clone-detector/analyze",
                files={
                    "original": (
                        "original.pdf",
                        b"%PDF-1.4 original",
                        "application/pdf",
                    ),
                    "comparison": (
                        "comparison.pdf",
                        b"%PDF-1.4 comparison",
                        "application/pdf",
                    ),
                },
            )
        self.assertEqual(response.status_code, 200, response.text)
        history = self.client.get("/api/clone-detector/checks")
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(history.json()["total"], 1)
        self.assertEqual(history.json()["items"][0]["similarity_percent"], 50.0)

    def test_ordinary_admin_cannot_create_a_manual_trademark_subscription(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        response = self.client.post(
            "/api/admin/subscriptions",
            json={
                "tenant_id": self.tenant_b.id,
                "plan_id": self.plan.id,
                "duration_days": 240,
                "reason": "Approved enterprise subscription",
            },
        )

        self.assertEqual(response.status_code, 409, response.text)
        self.assertFalse(
            tenant_product_access(self.db, self.tenant_b.id, "trademark")[
                "has_access"
            ]
        )

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

    def test_trademark_subscription_cannot_be_renewed_without_payment(self):
        subscription = self.add_subscription(
            status="expired", end_delta=timedelta(days=-10)
        )
        self.db.commit()
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin
        response = self.client.post(
            f"/api/admin/subscriptions/{subscription.id}/renew",
            json={
                "duration_days": 30,
                "reason": "Renewal approved",
            },
        )

        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(
            self.db.get(Subscription, subscription.id).status,
            "expired",
        )

    def test_ordinary_admin_can_list_subscription_clients(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        response = self.client.get("/api/admin/subscription-clients")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["items"][0]["id"], self.user.id)

    def test_manual_subscription_can_select_client_without_tenant(self):
        client_without_tenant = User(
            username="legacy-client",
            email="legacy-client@example.test",
            password_hash="not-used",
            display_name="Legacy Client",
            is_active=True,
            is_admin=False,
            is_super_admin=False,
            account_status="ACTIVE",
        )
        workforce_plan = SubscriptionPlan(
            code="AUTONOMOUS_WORKFORCE",
            product_key="workforce",
            name="Workforce",
            description="Test plan",
            monthly_price=Decimal("100.00"),
            currency="USD",
            billing_cycle="monthly",
            is_active=True,
        )
        self.db.add_all((client_without_tenant, workforce_plan))
        self.db.commit()
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        clients_response = self.client.get("/api/admin/subscription-clients")
        self.assertEqual(clients_response.status_code, 200, clients_response.text)
        listed_client = next(
            item
            for item in clients_response.json()["items"]
            if item["id"] == client_without_tenant.id
        )
        self.assertIsNone(listed_client["tenant_id"])

        response = self.client.post(
            "/api/admin/subscriptions",
            json={
                "client_id": client_without_tenant.id,
                "plan_id": workforce_plan.id,
                "duration_days": 30,
                "reason": "Approved by management",
            },
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.db.expire_all()
        self.assertIsNotNone(
            self.db.get(User, client_without_tenant.id).tenant_id
        )
        self.assertEqual(
            response.json()["tenant_id"],
            self.db.get(User, client_without_tenant.id).tenant_id,
        )

    def test_admin_subscription_statistics_include_revenue_trend_and_expiring_soon(self):
        expiring = self.add_subscription(end_delta=timedelta(days=5))
        self.add_subscription(end_delta=timedelta(days=45))
        payment = self.add_payment(expiring)
        payment.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
        pending_subscription = self.add_subscription(status="pending")
        self.add_payment(pending_subscription, status="pending")
        self.db.commit()
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin

        response = self.client.get("/api/admin/subscription-statistics")

        self.assertEqual(response.status_code, 200, response.text)
        statistics = response.json()
        self.assertEqual(statistics["active_subscriptions"], 2)
        self.assertEqual(statistics["pending_payment_requests"], 1)
        self.assertEqual(statistics["expiring_soon_count"], 1)
        self.assertEqual(statistics["expiring_soon"][0]["id"], expiring.id)
        self.assertEqual(statistics["expiring_soon"][0]["tenant_name"], "Tenant A")
        self.assertEqual(statistics["monthly_revenue_by_currency"]["USD"], "10.00")
        self.assertEqual(len(statistics["revenue_history"]), 6)
        self.assertEqual(statistics["revenue_history"][-1]["amount"], "10.00")

    def test_admin_can_trigger_expiry_emails_when_delivery_is_enabled(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin
        with patch("app.api.subscriptions.settings.email_enabled", True), patch(
            "app.api.subscriptions.send_expiry_reminders",
            return_value=(2, 1),
        ) as send_reminders:
            response = self.client.post("/api/admin/subscription-reminders")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"processed": 2, "email_failures": 1})
        send_reminders.assert_called_once()

    def test_admin_cannot_trigger_expiry_emails_when_delivery_is_disabled(self):
        api.dependency_overrides[get_current_user] = lambda: self.regular_admin
        with patch("app.api.subscriptions.settings.email_enabled", False), patch(
            "app.api.subscriptions.send_expiry_reminders"
        ) as send_reminders:
            response = self.client.post("/api/admin/subscription-reminders")

        self.assertEqual(response.status_code, 503, response.text)
        send_reminders.assert_not_called()

    def test_super_administrator_can_use_platform_admin_routes(self):
        api.dependency_overrides[get_current_user] = lambda: self.super_admin
        response = self.client.get("/api/admin/accounts")
        self.assertEqual(response.status_code, 200)

    def test_launch_code_is_hash_only_and_one_time(self):
        subscription = self.add_subscription()
        self.add_payment(subscription)
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
