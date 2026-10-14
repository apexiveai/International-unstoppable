from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.authorization import require_admin
from app.database import get_db
from app.models import (
    Payment,
    Subscription,
    SubscriptionPlan,
    User,
)
from app.models.payment import PaymentMethod
from app.services.audit_service import write_audit_log
from app.services.product_access import PUBLISHED_PRODUCT_KEYS

router = APIRouter(prefix="/api", tags=["Payments"])


class PaymentCreateRequest(BaseModel):
    plan_id: int = Field(gt=0)
    payment_method: str = Field(min_length=2, max_length=50)


class PaymentRejectRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


def _serialize_payment(payment: Payment) -> dict:
    return {
        "id": payment.id,
        "tenant_id": payment.tenant_id,
        "plan_id": payment.plan_id,
        "subscription_id": payment.subscription_id,
        "provider": payment.provider,
        "payment_method": payment.payment_method,
        "status": payment.status,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "checkout_reference": payment.checkout_reference,
        "external_payment_id": payment.external_payment_id,
        "failure_reason": payment.failure_reason,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
    }


def _get_payment(db: Session, payment_id: int) -> Payment:
    payment = db.scalar(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found.")
    return payment


@router.post("/payments/create", status_code=status.HTTP_201_CREATED)
@router.post("/payments", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_payment(
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a tenant.",
        )
    plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == payload.plan_id,
            SubscriptionPlan.is_active.is_(True),
        )
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Active subscription plan not found.")
    if plan.product_key not in PUBLISHED_PRODUCT_KEYS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This plan is not available for product access yet.",
        )
    payment_method = payload.payment_method.strip().lower()
    if payment_method not in {method.value for method in PaymentMethod}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported payment method.",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    subscription = Subscription(
        tenant_id=user.tenant_id,
        plan_id=plan.id,
        status="pending",
        price=plan.monthly_price,
        currency=plan.currency,
        billing_cycle=plan.billing_cycle,
        start_date=now,
    )
    db.add(subscription)
    db.flush()
    payment = Payment(
        tenant_id=user.tenant_id,
        plan_id=plan.id,
        subscription_id=subscription.id,
        provider=payment_method,
        payment_method=payment_method,
        status="pending",
        amount=plan.monthly_price,
        currency=plan.currency,
        checkout_reference=f"APX-{secrets.token_urlsafe(18)}",
        created_at=now,
        updated_at=now,
    )
    db.add(payment)
    db.flush()
    write_audit_log(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="payment.created",
        target_type="payment",
        target_id=payment.id,
        new_value={
            "plan_id": plan.id,
            "subscription_id": subscription.id,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "payment_method": payment.payment_method,
        },
    )
    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)


@router.get("/payments/me")
def get_my_payments(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant.")
    payments = db.scalars(
        select(Payment)
        .where(Payment.tenant_id == user.tenant_id)
        .order_by(desc(Payment.created_at))
        .limit(limit)
    ).all()
    return {
        "items": [_serialize_payment(payment) for payment in payments],
        "count": len(payments),
    }


@router.get("/payments/{payment_id}")
def get_my_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant.")
    payment = db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.tenant_id == user.tenant_id,
        )
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found.")
    return _serialize_payment(payment)


@router.get("/admin/payments")
def admin_list_payments(
    payment_status: str | None = Query(default=None, alias="status"),
    tenant_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = select(Payment)
    if payment_status:
        query = query.where(Payment.status == payment_status.strip().lower())
    if tenant_id is not None:
        query = query.where(Payment.tenant_id == tenant_id)
    payments = db.scalars(
        query.order_by(desc(Payment.created_at)).limit(limit)
    ).all()
    return {
        "items": [_serialize_payment(payment) for payment in payments],
        "count": len(payments),
    }


@router.get("/admin/payments/{payment_id}")
def admin_get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found.")
    return _serialize_payment(payment)


@router.post("/admin/payments/{payment_id}/verify")
def verify_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    payment = _get_payment(db, payment_id)
    if payment.status == "verified":
        return _serialize_payment(payment)
    if payment.status in {"rejected", "refunded", "cancelled"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment in status '{payment.status}' cannot be verified.",
        )
    old_status = payment.status
    payment.status = "verified"
    payment.failure_reason = None
    payment.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
    write_audit_log(
        db,
        tenant_id=payment.tenant_id,
        actor_user_id=admin.id,
        action="payment.verified",
        target_type="payment",
        target_id=payment.id,
        old_value={"status": old_status},
        new_value={"status": payment.status},
    )
    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)


@router.post("/admin/payments/{payment_id}/reject")
def reject_payment(
    payment_id: int,
    payload: PaymentRejectRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    payment = _get_payment(db, payment_id)
    if payment.status == "verified":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A verified payment cannot be rejected.",
        )
    if payment.status == "refunded":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A refunded payment cannot be rejected.",
        )
    old_status = payment.status
    payment.status = "rejected"
    payment.failure_reason = payload.reason.strip()
    payment.paid_at = None
    write_audit_log(
        db,
        tenant_id=payment.tenant_id,
        actor_user_id=admin.id,
        action="payment.rejected",
        target_type="payment",
        target_id=payment.id,
        old_value={"status": old_status},
        new_value={"status": payment.status, "reason": payment.failure_reason},
    )
    subscription = (
        db.get(Subscription, payment.subscription_id)
        if payment.subscription_id is not None
        else None
    )
    if subscription is not None and subscription.status == "pending":
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
        write_audit_log(
            db,
            tenant_id=subscription.tenant_id,
            actor_user_id=admin.id,
            action="subscription.cancelled",
            target_type="subscription",
            target_id=subscription.id,
            old_value={"status": "pending"},
            new_value={"status": "cancelled", "reason": "payment rejected"},
        )
    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)


@router.post("/admin/payments/{payment_id}/refund")
def refund_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    payment = _get_payment(db, payment_id)
    if payment.status != "verified":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only verified payments can be refunded.",
        )
    payment.status = "refunded"
    subscription = (
        db.get(Subscription, payment.subscription_id)
        if payment.subscription_id is not None
        else None
    )
    if subscription is not None and subscription.status == "active":
        subscription.status = "suspended"
        write_audit_log(
            db,
            tenant_id=subscription.tenant_id,
            actor_user_id=admin.id,
            action="subscription.suspended",
            target_type="subscription",
            target_id=subscription.id,
            old_value={"status": "active"},
            new_value={"status": "suspended", "reason": "payment refunded"},
        )
    write_audit_log(
        db,
        tenant_id=payment.tenant_id,
        actor_user_id=admin.id,
        action="payment.refunded",
        target_type="payment",
        target_id=payment.id,
        old_value={"status": "verified"},
        new_value={"status": "refunded"},
    )
    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)
