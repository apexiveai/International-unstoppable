from __future__ import annotations

import hashlib
import csv
import io
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from fastapi.responses import Response
from sqlalchemy import desc, func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.auth import create_access_token, get_current_user
from app.core.authorization import (
    can_bypass_product_entitlement,
    require_admin,
    require_subscription_operator,
    require_super_admin,
)
from app.core.config import settings
from app.database import get_db
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
from app.services.audit_service import write_audit_log, write_system_audit_event
from app.services.subscription_notifications import (
    queue_tenant_notification,
    send_tenant_subscription_email,
)
from app.services.subscription_reminders import send_expiry_reminders
from app.services.product_access import (
    PUBLISHED_PRODUCT_KEYS,
    build_product_response,
    product_is_published,
    require_product_key,
    require_tenant_product_access,
    tenant_product_access,
)

router = APIRouter(prefix="/api", tags=["Subscriptions"])


def _tenant_id(user: User) -> int:
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a tenant.",
        )
    return user.tenant_id


def _serialize_subscription(subscription: Subscription) -> dict:
    plan = subscription.plan
    return {
        "id": subscription.id,
        "tenant_id": subscription.tenant_id,
        "tenant_name": subscription.tenant.name if subscription.tenant else None,
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "price": str(subscription.price),
        "currency": subscription.currency,
        "billing_cycle": subscription.billing_cycle,
        "start_date": subscription.start_date,
        "current_period_end": subscription.current_period_end,
        "cancelled_at": subscription.cancelled_at,
        "admin_access_reason": subscription.admin_access_reason,
        "external_subscription_id": subscription.external_subscription_id,
        "plan": {
            "id": plan.id,
            "code": plan.code,
            "product_key": plan.product_key,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": str(plan.monthly_price),
            "currency": plan.currency,
            "billing_cycle": plan.billing_cycle,
            "is_active": plan.is_active,
            "minimum_contract_months": (
                8 if plan.code == "TRADEMARK_CONFLICT" else None
            ),
        },
        "contract_months": subscription.contract_months,
        "contract_end": subscription.contract_end,
    }


def _admin_subscription_status(
    subscription: Subscription, now: datetime | None = None
) -> str:
    if subscription.status == "active":
        now = now or datetime.now(timezone.utc).replace(tzinfo=None)
        period_end = subscription.current_period_end
        if period_end is not None:
            if period_end.tzinfo is not None:
                period_end = period_end.astimezone(timezone.utc).replace(tzinfo=None)
            if period_end <= now:
                return "expired"
    return subscription.status


def _get_subscription(db: Session, subscription_id: int) -> Subscription:
    subscription = db.scalar(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(Subscription.id == subscription_id)
        .with_for_update()
    )
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    return subscription


@router.get("/subscriptions/plans")
def list_subscription_plans(db: Session = Depends(get_db)):
    plans = db.scalars(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .where(SubscriptionPlan.product_key.in_(PUBLISHED_PRODUCT_KEYS))
        .order_by(SubscriptionPlan.id)
    ).all()
    return [
        {
            "id": plan.id,
            "code": plan.code,
            "product_key": plan.product_key,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": str(plan.monthly_price),
            "currency": plan.currency,
            "billing_cycle": plan.billing_cycle,
            "is_active": plan.is_active,
            "minimum_contract_months": (
                8 if plan.code == "TRADEMARK_CONFLICT" else None
            ),
        }
        for plan in plans
    ]


@router.get("/subscriptions/me")
def get_my_subscriptions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    subscriptions = db.scalars(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(Subscription.tenant_id == _tenant_id(user))
        .order_by(desc(Subscription.created_at))
    ).all()
    return [_serialize_subscription(subscription) for subscription in subscriptions]


@router.post("/subscriptions/{subscription_id}/cancel")
def cancel_my_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    subscription = _get_subscription(db, subscription_id)
    if subscription.status == "cancelled":
        return _serialize_subscription(subscription)
    if subscription.status not in {"pending", "active", "suspended"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subscription cannot be cancelled.",
        )
    return _admin_change_status(
        db, admin, subscription, "cancelled", "subscription.cancelled"
    )


@router.get("/subscriptions/access/{product_key}")
def get_product_access(
    product_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_product_key(product_key)
    tenant_id = _tenant_id(user)
    access = (
        require_tenant_product_access(
            db, tenant_id, product_key, is_admin=user.is_admin
        )
        if can_bypass_product_entitlement(user)
        else _tenant_product_access(db, tenant_id, product_key)
    )
    return {
        **build_product_response(product_key),
        "tenant_id": tenant_id,
        **access,
    }


def _tenant_product_access(
    db: Session,
    tenant_id: int,
    product_key: str,
) -> dict:
    return tenant_product_access(db, tenant_id, product_key)


class EnterpriseGrantCreateRequest(BaseModel):
    tenant_id: int = Field(gt=0)
    product_key: str
    access_type: Literal["trial", "complimentary"]
    starts_at: datetime
    expires_at: datetime | None
    is_permanent: bool = False
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_access_period(self):
        if self.starts_at.tzinfo is None or self.starts_at.utcoffset() is None:
            raise ValueError("starts_at must include a timezone.")
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
                raise ValueError("expires_at must include a timezone.")
            if self.expires_at <= self.starts_at:
                raise ValueError("expires_at must be after starts_at.")
        if self.is_permanent:
            if self.access_type != "complimentary":
                raise ValueError("Permanent access is available only for complimentary grants.")
            if self.expires_at is not None:
                raise ValueError("Permanent grants cannot have an expiration date.")
        elif self.expires_at is None:
            raise ValueError("An expiration date is required for non-permanent grants.")
        return self


class ProductLaunchCodeExchangeRequest(BaseModel):
    code: str = Field(min_length=32, max_length=128)


def _serialize_product_grant(grant: ProductAccessGrant) -> dict:
    return {
        "id": grant.id,
        "tenant_id": grant.tenant_id,
        "product_key": grant.product_key,
        "access_type": grant.access_type,
        "starts_at": grant.starts_at,
        "expires_at": grant.expires_at,
        "is_permanent": grant.is_permanent,
        "reason": grant.reason,
        "granted_by_id": grant.granted_by_id,
        "created_at": grant.created_at,
        "revoked_at": grant.revoked_at,
        "revoked_by_id": grant.revoked_by_id,
    }


@router.get("/admin/product-grants")
def list_product_grants(
    tenant_id: int | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    query = select(ProductAccessGrant)
    if tenant_id is not None:
        query = query.where(ProductAccessGrant.tenant_id == tenant_id)
    grants = db.scalars(
        query.order_by(desc(ProductAccessGrant.created_at)).limit(500)
    ).all()
    return {"items": [_serialize_product_grant(grant) for grant in grants]}


@router.post("/admin/product-grants", status_code=status.HTTP_201_CREATED)
def create_product_grant(
    payload: EnterpriseGrantCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    require_product_key(payload.product_key)
    if not product_is_published(payload.product_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This product is not published for access grants.",
        )
    if payload.product_key == "trademark":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trademark Conflict access requires a verified subscription payment.",
        )
    if db.get(Tenant, payload.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    grant = ProductAccessGrant(
        tenant_id=payload.tenant_id,
        product_key=payload.product_key,
        access_type=payload.access_type,
        starts_at=payload.starts_at.astimezone(timezone.utc),
        expires_at=(
            payload.expires_at.astimezone(timezone.utc)
            if payload.expires_at
            else None
        ),
        is_permanent=payload.is_permanent,
        reason=payload.reason.strip(),
        granted_by_id=admin.id,
    )
    db.add(grant)
    db.flush()
    write_audit_log(
        db,
        tenant_id=grant.tenant_id,
        actor_user_id=admin.id,
        action="product_access.granted",
        target_type="product_access_grant",
        target_id=grant.id,
        new_value=_serialize_product_grant(grant),
    )
    db.commit()
    db.refresh(grant)
    return _serialize_product_grant(grant)


@router.post("/admin/product-grants/{grant_id}/revoke")
def revoke_product_grant(
    grant_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    grant = db.get(ProductAccessGrant, grant_id, with_for_update=True)
    if grant is None:
        raise HTTPException(status_code=404, detail="Product access grant not found.")
    if grant.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product access grant has already been revoked.",
        )
    old_value = _serialize_product_grant(grant)
    grant.revoked_at = datetime.now(timezone.utc)
    grant.revoked_by_id = admin.id
    write_audit_log(
        db,
        tenant_id=grant.tenant_id,
        actor_user_id=admin.id,
        action="product_access.revoked",
        target_type="product_access_grant",
        target_id=grant.id,
        old_value=old_value,
        new_value=_serialize_product_grant(grant),
    )
    db.commit()
    db.refresh(grant)
    return _serialize_product_grant(grant)


@router.post("/subscriptions/products/{product_key}/launch")
def create_product_launch_code(
    product_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_product_key(product_key)
    tenant_id = _tenant_id(user)
    access = (
        require_tenant_product_access(
            db, tenant_id, product_key, is_admin=user.is_admin
        )
        if can_bypass_product_entitlement(user)
        else _tenant_product_access(db, tenant_id, product_key)
    )
    if not access["has_access"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active product access is required.",
        )
    now = datetime.now(timezone.utc)
    db.execute(
        update(ProductLaunchCode)
        .where(
            ProductLaunchCode.user_id == user.id,
            ProductLaunchCode.product_key == product_key,
            ProductLaunchCode.consumed_at.is_(None),
            ProductLaunchCode.revoked_at.is_(None),
            ProductLaunchCode.expires_at > now,
        )
        .values(revoked_at=now, revoked_by_id=user.id)
        .execution_options(synchronize_session=False)
    )
    raw_code = secrets.token_urlsafe(48)
    launch_code = ProductLaunchCode(
        code_hash=hashlib.sha256(raw_code.encode("utf-8")).hexdigest(),
        user_id=user.id,
        tenant_id=tenant_id,
        product_key=product_key,
        expires_at=now + timedelta(seconds=settings.product_launch_code_ttl_seconds),
    )
    db.add(launch_code)
    db.flush()
    write_audit_log(
        db,
        tenant_id=tenant_id,
        actor_user_id=user.id,
        action="product_launch_code.issued",
        target_type="product_launch_code",
        target_id=launch_code.code_hash[:16],
        new_value={"product_key": product_key, "expires_at": launch_code.expires_at},
    )
    db.commit()
    product_url = build_product_response(product_key)["url"]
    parsed_url = urlsplit(product_url)
    query = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    query["access_code"] = raw_code
    return {
        "url": urlunsplit(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                urlencode(query),
                parsed_url.fragment,
            )
        ),
        "expires_at": launch_code.expires_at,
    }


@router.post("/subscriptions/launch/exchange")
def exchange_product_launch_code(
    payload: ProductLaunchCodeExchangeRequest,
    db: Session = Depends(get_db),
):
    code_hash = hashlib.sha256(payload.code.encode("utf-8")).hexdigest()
    launch_code = db.scalar(
        select(ProductLaunchCode)
        .where(ProductLaunchCode.code_hash == code_hash)
    )
    now = datetime.now(timezone.utc)
    expires_at = launch_code.expires_at if launch_code is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if (
        launch_code is None
        or launch_code.consumed_at is not None
        or launch_code.revoked_at is not None
        or expires_at <= now
    ):
        write_system_audit_event(
            db,
            actor_user_id=launch_code.user_id if launch_code else None,
            tenant_id=launch_code.tenant_id if launch_code else None,
            action="product_launch_code.redemption_rejected",
            target_type="product_launch_code",
            target_id=code_hash[:16],
            outcome="rejected",
            details={"reason": "invalid_expired_consumed_or_revoked"},
        )
        if launch_code is not None:
            write_audit_log(
                db,
                tenant_id=launch_code.tenant_id,
                actor_user_id=launch_code.user_id,
                action="product_launch_code.redemption_rejected",
                target_type="product_launch_code",
                target_id=launch_code.code_hash[:16],
                new_value={"reason": "inactive_or_expired"},
            )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Product launch link is invalid or expired. Open the product from your dashboard again.",
        )
    user = db.get(User, launch_code.user_id)
    if (
        user is None
        or not user.is_active
        or user.account_status != "ACTIVE"
        or user.tenant_id != launch_code.tenant_id
        or not (
            can_bypass_product_entitlement(user)
            or _tenant_product_access(
                db,
                launch_code.tenant_id,
                launch_code.product_key,
            )["has_access"]
        )
    ):
        write_system_audit_event(
            db,
            actor_user_id=launch_code.user_id,
            tenant_id=launch_code.tenant_id,
            action="product_launch_code.redemption_rejected",
            target_type="product_launch_code",
            target_id=launch_code.code_hash[:16],
            outcome="rejected",
            details={"reason": "account_or_entitlement_not_authorized"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is no longer authorized for the product.",
        )
    consumed = db.execute(
        update(ProductLaunchCode)
        .where(
            ProductLaunchCode.code_hash == code_hash,
            ProductLaunchCode.consumed_at.is_(None),
            ProductLaunchCode.revoked_at.is_(None),
            ProductLaunchCode.expires_at > now,
        )
        .values(consumed_at=now)
        .execution_options(synchronize_session=False)
    )
    if consumed.rowcount != 1:
        write_system_audit_event(
            db,
            actor_user_id=launch_code.user_id,
            tenant_id=launch_code.tenant_id,
            action="product_launch_code.redemption_rejected",
            target_type="product_launch_code",
            target_id=launch_code.code_hash[:16],
            outcome="rejected",
            details={"reason": "concurrent_or_repeated_redemption"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Product launch link is invalid or expired. Open the product from your dashboard again.",
        )
    write_audit_log(
        db,
        tenant_id=launch_code.tenant_id,
        actor_user_id=launch_code.user_id,
        action="product_launch_code.redeemed",
        target_type="product_launch_code",
        target_id=launch_code.code_hash[:16],
        new_value={"product_key": launch_code.product_key},
    )
    access_token = create_access_token(user.id)
    db.commit()
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_id": launch_code.tenant_id,
        "product_key": launch_code.product_key,
    }


@router.post("/admin/product-launch-codes/{code_hash}/revoke")
def revoke_product_launch_code(
    code_hash: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    if len(code_hash) != 64 or any(char not in "0123456789abcdef" for char in code_hash):
        raise HTTPException(status_code=404, detail="Launch code not found.")
    launch_code = db.get(ProductLaunchCode, code_hash, with_for_update=True)
    if launch_code is None:
        raise HTTPException(status_code=404, detail="Launch code not found.")
    if launch_code.consumed_at is not None or launch_code.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Launch code has already been consumed or revoked.",
        )
    now = datetime.now(timezone.utc)
    launch_code.revoked_at = now
    launch_code.revoked_by_id = admin.id
    write_audit_log(
        db,
        tenant_id=launch_code.tenant_id,
        actor_user_id=admin.id,
        action="product_launch_code.revoked",
        target_type="product_launch_code",
        target_id=launch_code.code_hash[:16],
        new_value={"product_key": launch_code.product_key},
    )
    db.commit()
    return {"revoked": True}


@router.get("/admin/product-launch-codes")
def list_product_launch_codes(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    codes = db.scalars(
        select(ProductLaunchCode)
        .order_by(desc(ProductLaunchCode.created_at))
        .limit(limit)
    ).all()
    return {
        "items": [
            {
                "code_hash": code.code_hash,
                "user_id": code.user_id,
                "tenant_id": code.tenant_id,
                "product_key": code.product_key,
                "expires_at": code.expires_at,
                "consumed_at": code.consumed_at,
                "revoked_at": code.revoked_at,
                "created_at": code.created_at,
            }
            for code in codes
        ]
    }


@router.get("/admin/subscriptions")
def admin_list_subscriptions(
    tenant_id: int | None = None,
    subscription_status: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    plan_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    query = (
        select(Subscription)
        .join(Tenant, Tenant.id == Subscription.tenant_id)
        .options(joinedload(Subscription.plan), joinedload(Subscription.tenant))
    )
    if tenant_id is not None:
        query = query.where(Subscription.tenant_id == tenant_id)
    if plan_id is not None:
        query = query.where(Subscription.plan_id == plan_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Tenant.name.ilike(term),
                Tenant.slug.ilike(term),
            )
        )
    if subscription_status:
        requested = subscription_status.strip().lower()
        if requested == "active":
            query = query.where(
                Subscription.status == "active",
                or_(
                    Subscription.current_period_end.is_(None),
                    Subscription.current_period_end > now,
                ),
            )
        elif requested == "expired":
            query = query.where(
                or_(
                    Subscription.status == "expired",
                    (
                        (Subscription.status == "active")
                        & (Subscription.current_period_end <= now)
                    ),
                )
            )
        else:
            query = query.where(Subscription.status == requested)
    count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    subscriptions = db.scalars(
        query.order_by(desc(Subscription.created_at)).limit(limit).offset(offset)
    ).all()
    return {
        "items": [
            {**_serialize_subscription(item), "status": _admin_subscription_status(item, now)}
            for item in subscriptions
        ],
        "count": count,
        "limit": limit,
        "offset": offset,
    }


@router.get("/admin/subscription-statistics")
def admin_subscription_statistics(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_start = month_start
    for _ in range(5):
        revenue_start = (
            revenue_start.replace(year=revenue_start.year - 1, month=12)
            if revenue_start.month == 1
            else revenue_start.replace(month=revenue_start.month - 1)
        )
    active_count = db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status == "active",
            or_(
                Subscription.current_period_end.is_(None),
                Subscription.current_period_end > now,
            ),
        )
    ) or 0
    expired_count = db.scalar(
        select(func.count(Subscription.id)).where(
            or_(
                Subscription.status == "expired",
                (
                    (Subscription.status == "active")
                    & (Subscription.current_period_end <= now)
                ),
            )
        )
    ) or 0
    pending_payments = db.scalar(
        select(func.count(Payment.id)).where(
            Payment.status.in_(("pending", "processing"))
        )
    ) or 0
    next_month = (
        datetime(month_start.year + 1, 1, 1)
        if month_start.month == 12
        else datetime(month_start.year, month_start.month + 1, 1)
    )
    revenue_by_currency = db.execute(
        select(Payment.currency, func.sum(Payment.amount))
        .where(
            Payment.status == "verified",
            Payment.paid_at >= month_start,
            Payment.paid_at < next_month,
        )
        .group_by(Payment.currency)
        .order_by(Payment.currency)
    ).all()
    revenue_history_rows = db.execute(
        select(
            func.extract("year", Payment.paid_at),
            func.extract("month", Payment.paid_at),
            Payment.currency,
            func.sum(Payment.amount),
        )
        .where(
            Payment.status == "verified",
            Payment.paid_at >= revenue_start,
            Payment.paid_at < next_month,
        )
        .group_by(
            func.extract("year", Payment.paid_at),
            func.extract("month", Payment.paid_at),
            Payment.currency,
        )
        .order_by(
            func.extract("year", Payment.paid_at),
            func.extract("month", Payment.paid_at),
            Payment.currency,
        )
    ).all()
    revenue_months = []
    current_month = revenue_start
    while current_month < next_month:
        revenue_months.append(current_month.strftime("%Y-%m"))
        current_month = (
            current_month.replace(year=current_month.year + 1, month=1)
            if current_month.month == 12
            else current_month.replace(month=current_month.month + 1)
        )
    revenue_by_month_currency = {
        (f"{int(year):04d}-{int(month):02d}", currency): str(amount)
        for year, month, currency, amount in revenue_history_rows
    }
    revenue_currencies = sorted({currency for _, currency in revenue_by_month_currency})
    revenue_history = [
        {
            "month": month,
            "currency": currency,
            "amount": revenue_by_month_currency.get((month, currency), "0"),
        }
        for month in revenue_months
        for currency in revenue_currencies
    ]
    expiring_soon_query = (
        select(Subscription)
        .options(joinedload(Subscription.plan), joinedload(Subscription.tenant))
        .where(
            Subscription.status == "active",
            Subscription.current_period_end > now,
            Subscription.current_period_end <= now + timedelta(days=30),
        )
    )
    expiring_soon_count = db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status == "active",
            Subscription.current_period_end > now,
            Subscription.current_period_end <= now + timedelta(days=30),
        )
    ) or 0
    expiring_soon = db.scalars(
        expiring_soon_query.order_by(Subscription.current_period_end).limit(10)
    ).all()
    return {
        "active_subscriptions": active_count,
        "expired_subscriptions": expired_count,
        "monthly_revenue": (
            str(revenue_by_currency[0][1]) if len(revenue_by_currency) == 1 else None
        ),
        "currency": revenue_by_currency[0][0] if len(revenue_by_currency) == 1 else None,
        "monthly_revenue_by_currency": {
            currency: str(amount) for currency, amount in revenue_by_currency
        },
        "pending_payment_requests": pending_payments,
        "revenue_history": revenue_history,
        "expiring_soon_count": expiring_soon_count,
        "expiring_soon": [
            {
                "id": item.id,
                "tenant_name": item.tenant.name,
                "plan_name": item.plan.name,
                "current_period_end": item.current_period_end,
            }
            for item in expiring_soon
        ],
        "email_enabled": settings.email_enabled,
    }


@router.post("/admin/subscription-reminders")
def admin_send_subscription_reminders(
    _admin: User = Depends(require_subscription_operator),
    db: Session = Depends(get_db),
):
    if not settings.email_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscription email delivery is disabled. Configure EMAIL_ENABLED and SMTP settings first.",
        )
    processed, email_failures = send_expiry_reminders(db)
    return {
        "processed": processed,
        "email_failures": email_failures,
    }


@router.get("/admin/subscriptions/{subscription_id}")
def admin_get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return _serialize_subscription(_get_subscription(db, subscription_id))


@router.get("/admin/subscriptions/{subscription_id}/details")
def admin_subscription_details(
    subscription_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    subscription = _get_subscription(db, subscription_id)
    payments = db.scalars(
        select(Payment)
        .where(
            Payment.tenant_id == subscription.tenant_id,
            or_(
                Payment.subscription_id == subscription.id,
                (
                    (Payment.subscription_id.is_(None))
                    & (Payment.plan_id == subscription.plan_id)
                ),
            ),
        )
        .order_by(desc(Payment.created_at))
    ).all()
    audit_rows = db.execute(
        select(TenantAuditLog, User.display_name, User.username)
        .outerjoin(User, User.id == TenantAuditLog.actor_id)
        .where(
            TenantAuditLog.entity_type == "subscription",
            TenantAuditLog.entity_id == str(subscription.id),
        )
        .order_by(desc(TenantAuditLog.created_at))
        .limit(200)
    ).all()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return {
        **_serialize_subscription(subscription),
        "remaining_days": _subscription_remaining_days(subscription, now),
        "payment_history": [
            {
                "id": payment.id,
                "status": payment.status,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "payment_method": payment.payment_method,
                "paid_at": payment.paid_at,
                "created_at": payment.created_at,
            }
            for payment in payments
        ],
        "activity_log": [
            {
                "id": log.id,
                "actor_user_id": log.actor_id,
                "actor_name": display_name or username or "System",
                "action": log.action,
                "reason": log.new_value or log.details,
                "created_at": log.created_at,
                "old_value": log.old_value,
                "new_value": log.new_value,
            }
            for log, display_name, username in audit_rows
        ],
    }


@router.post("/admin/subscription-bulk-actions")
def admin_bulk_subscriptions(
    payload: BulkSubscriptionRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    subscriptions = db.scalars(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(Subscription.id.in_(payload.subscription_ids))
        .with_for_update()
    ).all()
    if len(subscriptions) != len(payload.subscription_ids):
        raise HTTPException(status_code=404, detail="One or more subscriptions were not found.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if payload.action == "extend":
        for subscription in subscriptions:
            if subscription.status not in {"active", "expired"}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Subscription #{subscription.id} cannot be extended.",
                )
            if (
                subscription.plan.code == "TRADEMARK_CONFLICT"
                or not product_is_published(subscription.plan.product_key)
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Subscription #{subscription.id} requires payment-based renewal.",
                )
        for subscription in subscriptions:
            old_end = subscription.current_period_end
            if old_end is not None and old_end.tzinfo is not None:
                old_end = old_end.astimezone(timezone.utc).replace(tzinfo=None)
            start = max(now, old_end) if old_end is not None else now
            previous_status = subscription.status
            subscription.status = "active"
            subscription.start_date = now if previous_status == "expired" else subscription.start_date
            subscription.current_period_end = start + timedelta(days=payload.duration_days or 30)
            subscription.cancelled_at = None
            write_audit_log(
                db,
                tenant_id=subscription.tenant_id,
                actor_user_id=admin.id,
                action="subscription.bulk_extended",
                target_type="subscription",
                target_id=subscription.id,
                old_value={"status": previous_status, "current_period_end": old_end},
                new_value={
                    "status": "active",
                    "current_period_end": subscription.current_period_end,
                    "duration_days": payload.duration_days,
                    "reason": payload.reason.strip(),
                },
            )
    else:
        for subscription in subscriptions:
            if subscription.status not in {"pending", "active", "suspended"}:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Subscription #{subscription.id} cannot be cancelled.",
                )
        for subscription in subscriptions:
            previous_status = subscription.status
            subscription.status = "cancelled"
            subscription.cancelled_at = now
            write_audit_log(
                db,
                tenant_id=subscription.tenant_id,
                actor_user_id=admin.id,
                action="subscription.bulk_cancelled",
                target_type="subscription",
                target_id=subscription.id,
                old_value={"status": previous_status},
                new_value={"status": "cancelled", "reason": payload.reason.strip()},
            )
    db.commit()
    return {
        "action": payload.action,
        "count": len(subscriptions),
        "subscription_ids": payload.subscription_ids,
    }


@router.get("/admin/subscriptions/export/csv")
def admin_export_subscriptions_csv(
    search: str | None = None,
    subscription_status: str | None = Query(default=None, alias="status"),
    plan_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        ["ID", "Tenant", "Plan", "Status", "Price", "Currency", "Start date", "End date", "Remaining days"]
    )
    for item in _subscription_export_rows(
        db, search=search, subscription_status=subscription_status, plan_id=plan_id
    ):
        writer.writerow(
            [
                item.id,
                item.tenant.name if item.tenant else item.tenant_id,
                item.plan.name,
                item.status,
                item.price,
                item.currency,
                item.start_date.isoformat() if item.start_date else "",
                item.current_period_end.isoformat() if item.current_period_end else "",
                _subscription_remaining_days(item, now),
            ]
        )
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="subscriptions.csv"'},
    )


@router.get("/admin/subscriptions/export/xlsx")
def admin_export_subscriptions_xlsx(
    search: str | None = None,
    subscription_status: str | None = Query(default=None, alias="status"),
    plan_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    import xlsxwriter

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    worksheet = workbook.add_worksheet("Subscriptions")
    headers = [
        "ID", "Tenant", "Plan", "Status", "Price", "Currency",
        "Start date", "End date", "Remaining days",
    ]
    for column, header in enumerate(headers):
        worksheet.write(0, column, header)
    for row, item in enumerate(
        _subscription_export_rows(
            db, search=search, subscription_status=subscription_status, plan_id=plan_id
        ),
        start=1,
    ):
        values = [
            item.id,
            item.tenant.name if item.tenant else str(item.tenant_id),
            item.plan.name,
            item.status,
            float(item.price),
            item.currency,
            item.start_date.isoformat() if item.start_date else "",
            item.current_period_end.isoformat() if item.current_period_end else "",
            _subscription_remaining_days(item, now),
        ]
        for column, value in enumerate(values):
            worksheet.write(row, column, value)
    workbook.close()
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="subscriptions.xlsx"'},
    )


@router.get("/admin/revenue-report.csv")
def admin_revenue_report_csv(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = datetime(year or now.year, month or now.month, 1)
    next_month = (
        datetime(start.year + 1, 1, 1)
        if start.month == 12
        else datetime(start.year, start.month + 1, 1)
    )
    totals = db.execute(
        select(Payment.currency, func.sum(Payment.amount), func.count(Payment.id))
        .where(
            Payment.status == "verified",
            Payment.paid_at >= start,
            Payment.paid_at < next_month,
        )
        .group_by(Payment.currency)
        .order_by(Payment.currency)
    ).all()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Period", "Currency", "Revenue", "Verified payments"])
    for currency, amount, count in totals:
        writer.writerow([start.strftime("%Y-%m"), currency, amount, count])
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="revenue-report.csv"'},
    )


class ActivateSubscriptionRequest(BaseModel):
    payment_id: int | None = Field(default=None, gt=0)
    duration_days: int = Field(default=30, ge=1, le=3660)
    override_verified_payment: bool = False
    override_reason: str | None = Field(default=None, min_length=3, max_length=2000)

    @model_validator(mode="after")
    def require_override_reason(self):
        if (
            self.override_verified_payment
            and len((self.override_reason or "").strip()) < 3
        ):
            raise ValueError(
                "A reason is required when overriding payment verification."
            )
        return self


class AdminSubscriptionPriceRequest(BaseModel):
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class AdminSubscriptionCreateRequest(BaseModel):
    tenant_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)
    duration_days: int = Field(default=30, ge=1, le=3660)
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_reason(self):
        if len(self.reason.strip()) < 3:
            raise ValueError("An approval reason is required.")
        return self


class AdminSubscriptionRenewRequest(BaseModel):
    duration_days: int = Field(default=30, ge=1, le=3660)
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_reason(self):
        if len(self.reason.strip()) < 3:
            raise ValueError("An approval reason is required.")
        return self


class AdminSubscriptionCancelRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_reason(self):
        if len(self.reason.strip()) < 3:
            raise ValueError("A cancellation reason is required.")
        return self


class BulkSubscriptionRequest(BaseModel):
    action: Literal["extend", "cancel"]
    subscription_ids: list[int] = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=3, max_length=2000)
    duration_days: int | None = Field(default=None, ge=1, le=3660)

    @model_validator(mode="after")
    def validate_action_details(self):
        if len(self.reason.strip()) < 3:
            raise ValueError("A reason is required.")
        if self.action == "extend" and self.duration_days is None:
            raise ValueError("Duration is required for bulk extension.")
        if len(set(self.subscription_ids)) != len(self.subscription_ids):
            raise ValueError("Subscription IDs must be unique.")
        return self


def _subscription_remaining_days(subscription: Subscription, now: datetime) -> int | None:
    period_end = subscription.current_period_end
    if period_end is None:
        return None
    if period_end.tzinfo is not None:
        period_end = period_end.astimezone(timezone.utc).replace(tzinfo=None)
    return max(0, (period_end.date() - now.date()).days)


def _subscription_export_rows(
    db: Session,
    *,
    search: str | None,
    subscription_status: str | None,
    plan_id: int | None,
):
    query = (
        select(Subscription)
        .join(Tenant, Tenant.id == Subscription.tenant_id)
        .options(joinedload(Subscription.plan), joinedload(Subscription.tenant))
    )
    if plan_id is not None:
        query = query.where(Subscription.plan_id == plan_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(or_(Tenant.name.ilike(term), Tenant.slug.ilike(term)))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if subscription_status == "active":
        query = query.where(
            Subscription.status == "active",
            or_(
                Subscription.current_period_end.is_(None),
                Subscription.current_period_end > now,
            ),
        )
    elif subscription_status == "expired":
        query = query.where(
            or_(
                Subscription.status == "expired",
                (
                    (Subscription.status == "active")
                    & (Subscription.current_period_end <= now)
                ),
            )
        )
    elif subscription_status:
        query = query.where(Subscription.status == subscription_status)
    return db.scalars(query.order_by(desc(Subscription.created_at))).all()


@router.get("/admin/subscription-clients")
def admin_list_subscription_clients(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    clients = db.scalars(
        select(User)
        .where(User.is_admin.is_(False), User.tenant_id.is_not(None))
        .order_by(User.display_name, User.id)
    ).all()
    return {
        "items": [
            {
                "id": client.id,
                "tenant_id": client.tenant_id,
                "username": client.username,
                "email": client.email,
                "display_name": client.display_name,
            }
            for client in clients
        ]
    }


@router.post("/admin/subscriptions", status_code=status.HTTP_201_CREATED)
def admin_create_subscription(
    payload: AdminSubscriptionCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    tenant = db.get(Tenant, payload.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    plan = db.get(SubscriptionPlan, payload.plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(
            status_code=404, detail="Active subscription plan not found."
        )
    require_product_key(plan.product_key)
    if not product_is_published(plan.product_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This product is not published for subscription access.",
        )
    if plan.code == "TRADEMARK_CONFLICT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trademark Conflict access must be approved through payment verification.",
        )

    existing = db.scalar(
        select(Subscription.id).where(
            Subscription.tenant_id == tenant.id,
            Subscription.plan_id == plan.id,
            Subscription.status == "active",
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active subscription already exists for this plan.",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    subscription = Subscription(
        tenant_id=tenant.id,
        plan_id=plan.id,
        status="pending",
        price=plan.monthly_price,
        currency=plan.currency,
        billing_cycle=plan.billing_cycle,
        start_date=now,
        current_period_end=now + timedelta(days=payload.duration_days),
        admin_access_reason=payload.reason.strip(),
    )
    db.add(subscription)
    db.flush()
    write_audit_log(
        db,
        tenant_id=tenant.id,
        actor_user_id=admin.id,
        action="subscription.admin_created",
        target_type="subscription",
        target_id=subscription.id,
        new_value={
            "status": "pending",
            "plan_id": plan.id,
            "duration_days": payload.duration_days,
            "reason": payload.reason.strip(),
        },
    )
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(_get_subscription(db, subscription.id))


@router.post("/admin/subscriptions/{subscription_id}/approve-manual")
def approve_manual_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    subscription = _get_subscription(db, subscription_id)
    if subscription.status != "pending" or not subscription.admin_access_reason:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending manual subscriptions can be approved.",
        )
    if subscription.plan.code == "TRADEMARK_CONFLICT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trademark Conflict access requires verified payment.",
        )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if subscription.current_period_end is None or subscription.current_period_end <= now:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The manual subscription request has expired.",
        )
    existing = db.scalar(
        select(Subscription.id).where(
            Subscription.tenant_id == subscription.tenant_id,
            Subscription.plan_id == subscription.plan_id,
            Subscription.status == "active",
            Subscription.id != subscription.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active subscription already exists for this plan.",
        )
    subscription.status = "active"
    write_audit_log(
        db,
        tenant_id=subscription.tenant_id,
        actor_user_id=admin.id,
        action="subscription.manual_approved",
        target_type="subscription",
        target_id=subscription.id,
        old_value={"status": "pending"},
        new_value={
            "status": "active",
            "reason": subscription.admin_access_reason,
            "current_period_end": subscription.current_period_end.isoformat(),
        },
    )
    queue_tenant_notification(
        db,
        tenant_id=subscription.tenant_id,
        actor_id=admin.id,
        notification_type="subscription_activated",
        title="Subscription activated",
        message=f"{subscription.plan.name} access has been activated.",
        subscription_id=subscription.id,
    )
    db.commit()
    db.refresh(subscription)
    send_tenant_subscription_email(
        db,
        tenant_id=subscription.tenant_id,
        subject="Your subscription has been activated",
        message=f"Your {subscription.plan.name} subscription is now active.",
    )
    return _serialize_subscription(_get_subscription(db, subscription.id))


@router.post("/admin/subscriptions/{subscription_id}/renew")
def admin_renew_subscription(
    subscription_id: int,
    payload: AdminSubscriptionRenewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    subscription = _get_subscription(db, subscription_id)
    require_product_key(subscription.plan.product_key)
    if not product_is_published(subscription.plan.product_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This product is not published for subscription access.",
        )
    if subscription.plan.code == "TRADEMARK_CONFLICT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trademark Conflict renewals require a verified monthly payment.",
        )
    if subscription.status not in {"active", "expired"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active or expired subscriptions can be renewed.",
        )

    another_active = db.scalar(
        select(Subscription.id).where(
            Subscription.tenant_id == subscription.tenant_id,
            Subscription.plan_id == subscription.plan_id,
            Subscription.status == "active",
            Subscription.id != subscription.id,
        )
    )
    if another_active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another active subscription already exists for this plan.",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    old_end = subscription.current_period_end
    if old_end is not None and old_end.tzinfo is not None:
        old_end = old_end.astimezone(timezone.utc).replace(tzinfo=None)
    renewal_start = max(now, old_end) if old_end is not None else now
    previous_status = subscription.status
    if previous_status == "expired":
        subscription.start_date = now
    subscription.status = "active"
    subscription.current_period_end = renewal_start + timedelta(
        days=payload.duration_days
    )
    subscription.cancelled_at = None
    subscription.admin_access_reason = payload.reason.strip()
    write_audit_log(
        db,
        tenant_id=subscription.tenant_id,
        actor_user_id=admin.id,
        action="subscription.renewed",
        target_type="subscription",
        target_id=subscription.id,
        old_value={
            "status": previous_status,
            "current_period_end": old_end.isoformat() if old_end else None,
        },
        new_value={
            "status": subscription.status,
            "current_period_end": subscription.current_period_end.isoformat(),
            "duration_days": payload.duration_days,
            "reason": payload.reason.strip(),
        },
    )
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(subscription)


@router.post("/admin/subscriptions/{subscription_id}/activate")
def activate_subscription(
    subscription_id: int,
    payload: ActivateSubscriptionRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    subscription = _get_subscription(db, subscription_id)
    require_product_key(subscription.plan.product_key)
    if not product_is_published(subscription.plan.product_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This product is not published for purchase yet.",
        )
    if subscription.status == "active":
        return _serialize_subscription(subscription)
    if subscription.status not in {"pending", "suspended", "expired"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subscription cannot be activated.",
        )
    if payload.override_verified_payment and not admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a Super Admin can override verified payment requirements.",
        )
    if (
        subscription.plan.code == "TRADEMARK_CONFLICT"
        and payload.override_verified_payment
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trademark Conflict access cannot bypass verified payment.",
        )

    payment = None
    if not payload.override_verified_payment:
        payment_query = select(Payment).where(
            Payment.tenant_id == subscription.tenant_id,
            Payment.plan_id == subscription.plan_id,
            Payment.status == "verified",
        )
        if payload.payment_id is not None:
            payment_query = payment_query.where(Payment.id == payload.payment_id)
        else:
            payment_query = payment_query.where(
                Payment.subscription_id == subscription.id
            )
        payment = db.scalar(
            payment_query.order_by(desc(Payment.created_at)).with_for_update()
        )
        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A verified payment for this subscription is required.",
            )
        if payment.subscription_id not in {None, subscription.id}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The verified payment is already linked to another subscription.",
            )

    another_active = db.scalar(
        select(Subscription.id).where(
            Subscription.tenant_id == subscription.tenant_id,
            Subscription.plan_id == subscription.plan_id,
            Subscription.status == "active",
            Subscription.id != subscription.id,
        )
    )
    if another_active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active subscription already exists for this plan.",
        )

    previous_status = subscription.status
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    subscription.status = "active"
    subscription.start_date = now
    subscription.current_period_end = now + timedelta(days=payload.duration_days)
    subscription.cancelled_at = None
    subscription.admin_access_reason = (
        (payload.override_reason or "").strip()
        if payload.override_verified_payment
        else None
    )
    if payment is not None:
        payment.subscription_id = subscription.id
    write_audit_log(
        db,
        tenant_id=subscription.tenant_id,
        actor_user_id=admin.id,
        action="subscription.activated",
        target_type="subscription",
        target_id=subscription.id,
        old_value={"status": previous_status},
        new_value={
            "status": subscription.status,
            "payment_id": payment.id if payment else None,
            "payment_override": payload.override_verified_payment,
            "override_reason": (
                payload.override_reason.strip()
                if payload.override_reason
                else None
            ),
            "current_period_end": subscription.current_period_end.isoformat(),
        },
    )
    queue_tenant_notification(
        db,
        tenant_id=subscription.tenant_id,
        actor_id=admin.id,
        notification_type="subscription_activated",
        title="Subscription activated",
        message=f"{subscription.plan.name} access has been activated.",
        subscription_id=subscription.id,
    )
    db.commit()
    db.refresh(subscription)
    send_tenant_subscription_email(
        db,
        tenant_id=subscription.tenant_id,
        subject="Your subscription has been activated",
        message=f"Your {subscription.plan.name} subscription is now active.",
    )
    return _serialize_subscription(subscription)


@router.patch("/admin/subscriptions/{subscription_id}/price")
def admin_update_subscription_price(
    subscription_id: int,
    payload: AdminSubscriptionPriceRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    subscription = _get_subscription(db, subscription_id)
    if subscription.plan.code == "TRADEMARK_CONFLICT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The signed contract price snapshot cannot be changed.",
        )
    previous_price = str(subscription.price)
    subscription.price = payload.price
    write_audit_log(
        db,
        tenant_id=subscription.tenant_id,
        actor_user_id=admin.id,
        action="subscription.price_updated",
        target_type="subscription",
        target_id=subscription.id,
        old_value={"price": previous_price, "currency": subscription.currency},
        new_value={"price": str(payload.price), "currency": subscription.currency},
    )
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(subscription)


def _admin_change_status(
    db: Session,
    admin: User,
    subscription: Subscription,
    new_status: str,
    action: str,
    reason: str | None = None,
) -> dict:
    old_status = subscription.status
    subscription.status = new_status
    if new_status == "cancelled":
        subscription.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    write_audit_log(
        db,
        tenant_id=subscription.tenant_id,
        actor_user_id=admin.id,
        action=action,
        target_type="subscription",
        target_id=subscription.id,
        old_value={"status": old_status},
        new_value={"status": new_status, **({"reason": reason} if reason else {})},
    )
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(subscription)


@router.post("/admin/subscriptions/{subscription_id}/suspend")
def suspend_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    subscription = _get_subscription(db, subscription_id)
    if subscription.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active subscriptions can be suspended.",
        )
    return _admin_change_status(
        db, admin, subscription, "suspended", "subscription.suspended"
    )


@router.post("/admin/subscriptions/{subscription_id}/cancel")
def admin_cancel_subscription(
    subscription_id: int,
    payload: AdminSubscriptionCancelRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    subscription = _get_subscription(db, subscription_id)
    if subscription.status == "cancelled":
        return _serialize_subscription(subscription)
    if subscription.status not in {"pending", "active", "suspended"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subscription cannot be cancelled.",
        )
    return _admin_change_status(
        db,
        admin,
        subscription,
        "cancelled",
        "subscription.cancelled",
        payload.reason.strip(),
    )


@router.post("/admin/subscriptions/{subscription_id}/expire")
def expire_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    subscription = _get_subscription(db, subscription_id)
    if subscription.status == "expired":
        return _serialize_subscription(subscription)
    if subscription.status not in {"active", "suspended"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active or suspended subscriptions can be expired.",
        )
    return _admin_change_status(
        db, admin, subscription, "expired", "subscription.expired"
    )


@router.get("/admin/audit-logs")
def admin_audit_logs(
    tenant_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    query = select(TenantAuditLog)
    if tenant_id is not None:
        query = query.where(TenantAuditLog.tenant_id == tenant_id)
    logs = db.scalars(
        query.order_by(desc(TenantAuditLog.created_at)).limit(limit)
    ).all()
    return [
        {
            "id": log.id,
            "tenant_id": log.tenant_id,
            "actor_user_id": log.actor_user_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get("/admin/system-audit-logs")
def admin_system_audit_logs(
    tenant_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    query = select(SystemAuditEvent)
    if tenant_id is not None:
        query = query.where(SystemAuditEvent.tenant_id == tenant_id)
    events = db.scalars(
        query.order_by(desc(SystemAuditEvent.created_at)).limit(limit)
    ).all()
    return [
        {
            "id": event.id,
            "tenant_id": event.tenant_id,
            "actor_user_id": event.actor_user_id,
            "action": event.action,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "outcome": event.outcome,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in events
    ]
