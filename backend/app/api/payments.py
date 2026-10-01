from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.payment import (

    CreatePaymentRequest,

    PaymentResponse,

)

from app.services.payments import (

    create_checkout,

)

from app.services.payments.service import (

    create_payment,

    get_payment,

)

router = APIRouter(

    prefix="/api/payments",

    tags=["Payments"],

)

# Temporary development tenant resolver.

# Replace with authenticated JWT tenant resolution

# before production launch.

def get_current_tenant_id() -> int:

    return 1

@router.post(

    "/create",

    response_model=PaymentResponse,

    status_code=201,

)

def create_payment_endpoint(

    payload: CreatePaymentRequest,

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    return create_payment(

        db=db,

        tenant_id=tenant_id,

        plan_id=payload.plan_id,

        payment_method=payload.payment_method,

    )

@router.post(

    "/{payment_id}/checkout",

)

def checkout_payment_endpoint(

    payment_id: int,

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    payment = get_payment(

        db=db,

        tenant_id=tenant_id,

        payment_id=payment_id,

    )

    result = create_checkout(

        db=db,

        tenant_id=tenant_id,

        payment=payment,

    )

    return {

        "payment_id": payment.id,

        "provider": result.provider,

        "status": result.status,

        "checkout_url": result.checkout_url,

        "external_payment_id": (

            result.external_payment_id

        ),

        "message": result.message,

    }

@router.get(

    "/{payment_id}",

    response_model=PaymentResponse,

)

def get_payment_endpoint(

    payment_id: int,

    db: Session = Depends(get_db),

):

    tenant_id = get_current_tenant_id()

    return get_payment(

        db=db,

        tenant_id=tenant_id,

        payment_id=payment_id,

    )