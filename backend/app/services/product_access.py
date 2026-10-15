from __future__ import annotations

import calendar
from datetime import datetime, timezone

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment
from app.models.product_grant import ProductAccessGrant
from app.models.subscription import Subscription, SubscriptionPlan

PRODUCTS = {

    "trademark": {
        "name": "Trademark Conflict",
        "entitlement_code": "TRADEMARK_CONFLICT",
        "minimum_contract_months": 8,
        "url": "https://trademark.apexiveai.com",
    },

    "workforce": {
        "name": "Autonomous Workforce Agent",
        "entitlement_code": "AUTONOMOUS_WORKFORCE",
        "url": "https://workforce.apexiveai.com",
    },

    "max_myanmar": {
        "name": "MAX-MYANMAR",
        "entitlement_code": "MAX_MYANMAR",
        "url": "https://max.apexiveai.com",
    },

    "mna": {
        "name": "MYANMAR NATIONAL AIRLINES",
        "entitlement_code": "MNA_AIRLINES",
        "url": "https://mna.apexiveai.com",
    },
}

PUBLISHED_PRODUCT_KEYS = frozenset({"trademark", "workforce"})

ACTIVE_STATUS = "ACTIVE"

VERIFIED_PAYMENT = "VERIFIED"

def utc_now() -> datetime:

    return datetime.now(timezone.utc)


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def normalize(value: Any) -> str:

    return str(value or "").strip().upper()

def subscription_is_active(subscription: Any) -> bool:

    if subscription is None:

        return False

    if normalize(getattr(subscription, "status", "")) != ACTIVE_STATUS:

        return False

    now = utc_now()
    starts_at = getattr(subscription, "start_date", None)
    expires_at = getattr(subscription, "current_period_end", None)
    if expires_at is None:
        expires_at = getattr(subscription, "expires_at", None)
    contract_end = getattr(subscription, "contract_end", None)

    for boundary, is_start in (
        (starts_at, True),
        (expires_at, False),
        (contract_end, False),
    ):
        if boundary is None:
            continue
        if boundary.tzinfo is None:
            boundary = boundary.replace(tzinfo=timezone.utc)
        else:
            boundary = boundary.astimezone(timezone.utc)
        if (is_start and boundary > now) or (not is_start and boundary <= now):
            return False
    return True

def payment_is_verified(payment: Any) -> bool:

    if payment is None:

        return False

    return normalize(getattr(payment, "status", "")) == VERIFIED_PAYMENT


def can_access_product(subscription: Any, product_key: str) -> bool:
    if (
        product_key not in PUBLISHED_PRODUCT_KEYS
        or not subscription_is_active(subscription)
    ):
        return False
    product = PRODUCTS.get(product_key)
    if product is None:
        return False
    plan = getattr(subscription, "plan", None)
    subscription_code = getattr(subscription, "plan_code", None)
    if subscription_code is None:
        subscription_code = getattr(plan, "code", None)
    return subscription_code == product["entitlement_code"]


def product_is_published(product_key: str) -> bool:
    return product_key in PUBLISHED_PRODUCT_KEYS


def require_product_key(product_key: str) -> dict:

    product = PRODUCTS.get(product_key)

    if product is None:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,

            detail="Unknown product.",

        )

    return product

def require_active_subscription(

    subscription: Any,

    product_key: str,

) -> Any:

    require_product_key(product_key)

    if subscription is None:

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="No subscription found for this product.",

        )

    product = require_product_key(product_key)
    plan = getattr(subscription, "plan", None)
    subscription_code = getattr(subscription, "plan_code", None)
    if subscription_code is None:
        subscription_code = getattr(plan, "code", None)

    if subscription_code != product["entitlement_code"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription does not belong to this product.",
        )

    if not subscription_is_active(subscription):

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="Active subscription required.",

        )

    return subscription

def require_verified_payment(payment: Any) -> Any:

    if not payment_is_verified(payment):

        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,

            detail="Payment must be verified before subscription activation.",

        )

    return payment

def build_product_response(product_key: str) -> dict:

    product = require_product_key(product_key)

    return {

        "product_key": product_key,

        "product_name": product["name"],
        "entitlement_code": product["entitlement_code"],
        "minimum_contract_months": product.get("minimum_contract_months"),

        "url": product["url"],

    }


def tenant_product_access(
    db: Session,
    tenant_id: int,
    product_key: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    require_product_key(product_key)
    now = now or utc_now()

    product_subscriptions = (
        select(Subscription)
        .join(SubscriptionPlan)
        .options(joinedload(Subscription.plan))
        .where(
            Subscription.tenant_id == tenant_id,
            SubscriptionPlan.code == PRODUCTS[product_key]["entitlement_code"],
        )
    )
    active_subscription = db.scalar(
        product_subscriptions.where(Subscription.status == "active")
        .order_by(desc(Subscription.created_at))
        .limit(1)
    )
    latest_subscription = active_subscription or db.scalar(
        product_subscriptions.order_by(desc(Subscription.created_at)).limit(1)
    )

    verified_payment = (
        db.scalar(
            select(Payment.id).where(
                Payment.subscription_id == active_subscription.id,
                Payment.tenant_id == tenant_id,
                Payment.status == "verified",
            )
        )
        if active_subscription is not None
        else None
    )
    paid_access = bool(
        active_subscription
        and can_access_product(active_subscription, product_key)
        and (
            verified_payment is not None
            or (
                product_key != "trademark"
                and active_subscription.admin_access_reason is not None
            )
        )
    )
    grant = None if product_key == "trademark" else db.scalar(
        select(ProductAccessGrant)
        .where(
            ProductAccessGrant.tenant_id == tenant_id,
            ProductAccessGrant.product_key == product_key,
            ProductAccessGrant.starts_at <= now,
            ProductAccessGrant.revoked_at.is_(None),
            or_(
                ProductAccessGrant.is_permanent.is_(True),
                ProductAccessGrant.expires_at > now,
            ),
        )
        .order_by(desc(ProductAccessGrant.created_at))
        .limit(1)
    )

    return {
        "has_access": paid_access or grant is not None,
        "source": (
            "enterprise_grant"
            if grant
            else "subscription" if paid_access else None
        ),
        "grant_id": grant.id if grant else None,
        "access_type": grant.access_type if grant else None,
        "starts_at": grant.starts_at if grant else None,
        "expires_at": grant.expires_at if grant else None,
        "is_permanent": grant.is_permanent if grant else False,
        "subscription_id": latest_subscription.id if latest_subscription else None,
        "status": (
            "active"
            if grant
            else latest_subscription.status if latest_subscription else None
        ),
        "current_period_end": (
            grant.expires_at
            if grant
            else (
                latest_subscription.current_period_end
                if latest_subscription
                else None
            )
        ),
    }


def require_tenant_product_access(
    db: Session,
    tenant_id: int,
    product_key: str,
    *,
    is_admin: bool = False,
) -> dict[str, Any]:
    if is_admin:
        require_product_key(product_key)
        return {
            "has_access": True,
            "source": None,
            "grant_id": None,
            "access_type": None,
            "starts_at": None,
            "expires_at": None,
            "is_permanent": False,
            "subscription_id": None,
            "status": "active",
            "current_period_end": None,
        }
    access = tenant_product_access(db, tenant_id, product_key)
    if not access["has_access"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active product access is required.",
        )
    return access