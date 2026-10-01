from datetime import datetime, timedelta

from fastapi import HTTPException

from sqlalchemy import select

from sqlalchemy.orm import Session, joinedload

from app.models.subscription import Subscription, SubscriptionPlan

ACTIVE_STATUSES = {

    "trialing",

    "active",

}

def get_active_plans(db: Session) -> list[SubscriptionPlan]:

    stmt = (

        select(SubscriptionPlan)

        .where(SubscriptionPlan.is_active.is_(True))

        .order_by(SubscriptionPlan.monthly_price.asc())

    )

    return list(db.scalars(stmt).all())

def get_tenant_subscriptions(

    db: Session,

    tenant_id: int,

) -> list[Subscription]:

    stmt = (

        select(Subscription)

        .options(joinedload(Subscription.plan))

        .where(Subscription.tenant_id == tenant_id)

        .order_by(Subscription.created_at.desc())

    )

    return list(db.scalars(stmt).unique().all())

def get_subscription(

    db: Session,

    tenant_id: int,

    subscription_id: int,

) -> Subscription:

    stmt = (

        select(Subscription)

        .options(joinedload(Subscription.plan))

        .where(

            Subscription.id == subscription_id,

            Subscription.tenant_id == tenant_id,

        )

    )

    subscription = db.scalars(stmt).unique().first()

    if subscription is None:

        raise HTTPException(

            status_code=404,

            detail="Subscription not found",

        )

    return subscription

def create_subscription(

    db: Session,

    tenant_id: int,

    plan_id: int,

) -> Subscription:

    plan = db.get(SubscriptionPlan, plan_id)

    if plan is None or not plan.is_active:

        raise HTTPException(

            status_code=404,

            detail="Subscription plan not found",

        )

    # Prevent duplicate active subscriptions for the same product.

    stmt = (

        select(Subscription)

        .join(Subscription.plan)

        .where(

            Subscription.tenant_id == tenant_id,

            Subscription.plan_id == plan_id,

            Subscription.status.in_(ACTIVE_STATUSES),

        )

    )

    existing = db.scalars(stmt).first()

    if existing is not None:

        raise HTTPException(

            status_code=409,

            detail="This product is already subscribed",

        )

    start_date = datetime.utcnow()

    # Initial internal subscription period.

    # Real payment renewal/webhook logic will replace this later.

    current_period_end = start_date + timedelta(days=30)

    subscription = Subscription(

        tenant_id=tenant_id,

        plan_id=plan.id,

        status="active",

        price=plan.monthly_price,

        currency=plan.currency,

        billing_cycle=plan.billing_cycle,

        start_date=start_date,

        current_period_end=current_period_end,

    )

    db.add(subscription)

    db.commit()

    db.refresh(subscription)

    return get_subscription(

        db,

        tenant_id,

        subscription.id,

    )

def cancel_subscription(

    db: Session,

    tenant_id: int,

    subscription_id: int,

) -> Subscription:

    subscription = get_subscription(

        db,

        tenant_id,

        subscription_id,

    )

    if subscription.status not in ACTIVE_STATUSES:

        raise HTTPException(

            status_code=409,

            detail="Subscription is not active",

        )

    subscription.status = "cancelled"

    subscription.cancelled_at = datetime.utcnow()

    db.add(subscription)

    db.commit()

    db.refresh(subscription)

    return subscription

def check_product_access(

    db: Session,

    tenant_id: int,

    product_key: str,

) -> Subscription | None:

    stmt = (

        select(Subscription)

        .join(Subscription.plan)

        .options(joinedload(Subscription.plan))

        .where(

            Subscription.tenant_id == tenant_id,

            SubscriptionPlan.product_key == product_key,

            Subscription.status.in_(ACTIVE_STATUSES),

        )

        .order_by(Subscription.created_at.desc())

    )

    return db.scalars(stmt).unique().first()