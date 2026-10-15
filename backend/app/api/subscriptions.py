from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import desc, select, update
from sqlalchemy.orm import Session, joinedload

from app.auth import create_access_token, get_current_user
from app.core.authorization import require_admin
from app.core.authorization import require_super_admin
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
from app.services.product_access import (
    PUBLISHED_PRODUCT_KEYS,
    build_product_response,
    product_is_published,
    require_product_key,
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
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "price": str(subscription.price),
        "currency": subscription.currency,
        "billing_cycle": subscription.billing_cycle,
        "start_date": subscription.start_date,
        "current_period_end": subscription.current_period_end,
        "cancelled_at": subscription.cancelled_at,
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
    access = _tenant_product_access(db, tenant_id, product_key)
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
    access = _tenant_product_access(db, tenant_id, product_key)
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
        or not _tenant_product_access(
            db,
            launch_code.tenant_id,
            launch_code.product_key,
        )["has_access"]
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
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = select(Subscription).options(joinedload(Subscription.plan))
    if tenant_id is not None:
        query = query.where(Subscription.tenant_id == tenant_id)
    if subscription_status:
        query = query.where(
            Subscription.status == subscription_status.strip().lower()
        )
    subscriptions = db.scalars(
        query.order_by(desc(Subscription.created_at)).limit(limit)
    ).all()
    return {
        "items": [_serialize_subscription(item) for item in subscriptions],
        "count": len(subscriptions),
    }


@router.get("/admin/subscriptions/{subscription_id}")
def admin_get_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return _serialize_subscription(_get_subscription(db, subscription_id))


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
    admin: User = Depends(require_admin),
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
        status="active",
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
            "plan_id": plan.id,
            "duration_days": payload.duration_days,
            "reason": payload.reason.strip(),
        },
    )
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(_get_subscription(db, subscription.id))


@router.post("/admin/subscriptions/{subscription_id}/renew")
def admin_renew_subscription(
    subscription_id: int,
    payload: AdminSubscriptionRenewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
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
    admin: User = Depends(require_admin),
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
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(subscription)


@router.patch("/admin/subscriptions/{subscription_id}/price")
def admin_update_subscription_price(
    subscription_id: int,
    payload: AdminSubscriptionPriceRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
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
        new_value={"status": new_status},
    )
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(subscription)


@router.post("/admin/subscriptions/{subscription_id}/suspend")
def suspend_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
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


@router.post("/admin/subscriptions/{subscription_id}/expire")
def expire_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
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
