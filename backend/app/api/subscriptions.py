from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.subscription import (

    SubscribeRequest,

    SubscriptionAccessResponse,

    SubscriptionCancelResponse,

    SubscriptionPlanResponse,

    SubscriptionResponse,

)

from app.services.subscriptions import (

    cancel_subscription,

    check_product_access,

    create_subscription,

    get_active_plans,

    get_subscription,

    get_tenant_subscriptions,

)

router = APIRouter(

    prefix="/api/subscriptions",

    tags=["Subscriptions"],

)

# Temporary development tenant resolver.

#

# The existing authentication system will replace this with the

# authenticated user's tenant_id once the frontend subscription flow

# is connected to JWT authentication.

def get_current_tenant_id() -> int:

    return 1

@router.get(

    "/plans",

    response_model=list[SubscriptionPlanResponse],

)

def list_subscription_plans(

    db: Session = Depends(get_db),

):

    return get_active_plans(db)

@router.get(

    "/me",

    response_model=list[SubscriptionResponse],

)

def list_my_subscriptions(

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    return get_tenant_subscriptions(

        db,

        tenant_id,

    )

@router.post(

    "/subscribe",

    response_model=SubscriptionResponse,

    status_code=201,

)

def subscribe(

    payload: SubscribeRequest,

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    return create_subscription(

        db=db,

        tenant_id=tenant_id,

        plan_id=payload.plan_id,

    )

@router.post(

    "/{subscription_id}/cancel",

    response_model=SubscriptionCancelResponse,

)

def cancel(

    subscription_id: int,

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    subscription = cancel_subscription(

        db=db,

        tenant_id=tenant_id,

        subscription_id=subscription_id,

    )

    return subscription

@router.get(

    "/access/{product_key}",

    response_model=SubscriptionAccessResponse,

)

def product_access(

    product_key: str,

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    subscription = check_product_access(

        db=db,

        tenant_id=tenant_id,

        product_key=product_key,

    )

    if subscription is None:

        return SubscriptionAccessResponse(

            product_key=product_key,

            has_access=False,

        )

    return SubscriptionAccessResponse(

        product_key=product_key,

        has_access=True,

        subscription_id=subscription.id,

        status=subscription.status,

        current_period_end=subscription.current_period_end,

    )

@router.get(

    "/{subscription_id}",

    response_model=SubscriptionResponse,

)

def get_my_subscription(

    subscription_id: int,

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    return get_subscription(

        db=db,

        tenant_id=tenant_id,

        subscription_id=subscription_id,

    )