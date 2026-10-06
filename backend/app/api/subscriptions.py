from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.core.authorization import require_admin
from app.database import get_db
from app.models import Payment, Subscription, SubscriptionPlan, TenantAuditLog, User
from app.services.audit_service import write_audit_log
from app.services.product_access import (
    PUBLISHED_PRODUCT_KEYS,
    can_access_product,
    build_product_response,
    product_is_published,
    require_product_key,
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
            "product_key": plan.product_key,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": str(plan.monthly_price),
            "currency": plan.currency,
            "billing_cycle": plan.billing_cycle,
            "is_active": plan.is_active,
        },
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
            "product_key": plan.product_key,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": str(plan.monthly_price),
            "currency": plan.currency,
            "billing_cycle": plan.billing_cycle,
            "is_active": plan.is_active,
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
    user: User = Depends(get_current_user),
):
    subscription = _get_subscription(db, subscription_id)
    if subscription.tenant_id != _tenant_id(user):
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if subscription.status == "cancelled":
        return _serialize_subscription(subscription)
    if subscription.status not in {"pending", "active", "suspended"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subscription cannot be cancelled.",
        )
    old_status = subscription.status
    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    write_audit_log(
        db,
        tenant_id=subscription.tenant_id,
        actor_user_id=user.id,
        action="subscription.cancelled",
        target_type="subscription",
        target_id=subscription.id,
        old_value={"status": old_status},
        new_value={"status": subscription.status},
    )
    db.commit()
    db.refresh(subscription)
    return _serialize_subscription(subscription)


@router.get("/subscriptions/access/{product_key}")
def get_product_access(
    product_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = require_product_key(product_key)
    subscriptions_for_product = (
        select(Subscription)
        .join(SubscriptionPlan)
        .options(joinedload(Subscription.plan))
        .where(
            Subscription.tenant_id == _tenant_id(user),
            SubscriptionPlan.product_key == product_key,
        )
    )
    subscription = db.scalar(
        subscriptions_for_product.where(Subscription.status == "active")
        .order_by(desc(Subscription.created_at))
    )
    latest_subscription = subscription or db.scalar(
        subscriptions_for_product.order_by(desc(Subscription.created_at))
    )
    has_access = bool(
        subscription
        and can_access_product(subscription, product_key)
        and db.scalar(
            select(Payment.id).where(
                Payment.subscription_id == subscription.id,
                Payment.status == "verified",
            )
        )
    )
    return {
        **build_product_response(product_key),
        "has_access": has_access,
        "subscription_id": latest_subscription.id if latest_subscription else None,
        "status": latest_subscription.status if latest_subscription else None,
        "current_period_end": (
            latest_subscription.current_period_end if latest_subscription else None
        ),
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
            "payment_id": payment.id,
            "current_period_end": subscription.current_period_end.isoformat(),
        },
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
    _admin: User = Depends(require_admin),
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
