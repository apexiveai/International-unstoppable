from __future__ import annotations

import os

from datetime import datetime

from uuid import uuid4

from fastapi import HTTPException

from sqlalchemy import select

from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus

from app.models.subscription import SubscriptionPlan

from app.services.payments.aya import AYAPaymentProvider

from app.services.payments.base import (

    CheckoutRequest,

    CheckoutResponse,

)

from app.services.payments.cb import CBPaymentProvider

from app.services.payments.kbz import KBZPaymentProvider

SUPPORTED_METHODS = {

    "card",

    "mpu",

    "cbpay",

    "kbzpay",

    "ayapay",

}

PAYMENT_METHOD_PROVIDER_MAP = {

    "card": "cb_gateway",

    "mpu": "cb_gateway",

    "cbpay": "cb_gateway",

    "kbzpay": "kbzpay",

    "ayapay": "ayapay",

}

def get_provider(payment_method: str):

    payment_method = payment_method.lower().strip()

    provider_name = PAYMENT_METHOD_PROVIDER_MAP.get(

        payment_method

    )

    if provider_name is None:

        raise HTTPException(

            status_code=400,

            detail=(

                f"Unsupported payment method: "

                f"{payment_method}"

            ),

        )

    providers = {

        "cb_gateway": CBPaymentProvider(),

        "kbzpay": KBZPaymentProvider(),

        "ayapay": AYAPaymentProvider(),

    }

    provider = providers.get(provider_name)

    if provider is None:

        raise HTTPException(

            status_code=500,

            detail="Payment provider is not configured.",

        )

    return provider

def create_payment(

    db: Session,

    tenant_id: int,

    plan_id: int,

    payment_method: str,

) -> Payment:

    payment_method = payment_method.lower().strip()

    if payment_method not in SUPPORTED_METHODS:

        raise HTTPException(

            status_code=400,

            detail="Unsupported payment method",

        )

    provider = PAYMENT_METHOD_PROVIDER_MAP.get(

        payment_method

    )

    if provider is None:

        raise HTTPException(

            status_code=400,

            detail="No payment provider configured",

        )

    plan = db.get(

        SubscriptionPlan,

        plan_id,

    )

    if plan is None or not plan.is_active:

        raise HTTPException(

            status_code=404,

            detail="Subscription plan not found",

        )

    checkout_reference = (

        f"APX-"

        f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-"

        f"{uuid4().hex[:10].upper()}"

    )

    payment = Payment(

        tenant_id=tenant_id,

        plan_id=plan.id,

        subscription_id=None,

        provider=provider,

        payment_method=payment_method,

        status=PaymentStatus.PENDING.value,

        amount=plan.monthly_price,

        currency=plan.currency,

        checkout_reference=checkout_reference,

    )

    db.add(payment)

    db.commit()

    db.refresh(payment)

    return payment

def get_payment(

    db: Session,

    tenant_id: int,

    payment_id: int,

) -> Payment:

    stmt = select(Payment).where(

        Payment.id == payment_id,

        Payment.tenant_id == tenant_id,

    )

    payment = db.scalars(stmt).first()

    if payment is None:

        raise HTTPException(

            status_code=404,

            detail="Payment not found",

        )

    return payment

def create_checkout(

    db: Session,

    tenant_id: int,

    payment: Payment,

) -> CheckoutResponse:

    if payment.tenant_id != tenant_id:

        raise HTTPException(

            status_code=404,

            detail="Payment not found.",

        )

    if payment.status in {

        PaymentStatus.PAID.value,

        PaymentStatus.CANCELLED.value,

        PaymentStatus.REFUNDED.value,

    }:

        raise HTTPException(

            status_code=400,

            detail=(

                f"Payment cannot enter checkout "

                f"from status '{payment.status}'."

            ),

        )

    provider = get_provider(

        payment.payment_method
)

    frontend_url = os.getenv(

        "FRONTEND_URL",

        "https://www.apexiveai.com",

    ).rstrip("/")

    api_url = os.getenv(

        "API_PUBLIC_URL",

        "https://api.apexiveai.com",

    ).rstrip("/")

    request = CheckoutRequest(

        payment_id=payment.id,

        reference=payment.checkout_reference or "",

        amount=payment.amount,

        currency=payment.currency,

        payment_method=payment.payment_method,

        return_url=(

            f"{frontend_url}/payment/success"

            f"?payment_id={payment.id}"

        ),

        cancel_url=(

            f"{frontend_url}/checkout"

        ),

        webhook_url=(

            f"{api_url}/api/payments/webhook"

        ),

    )

    payment.status = PaymentStatus.PROCESSING.value

    payment.updated_at = datetime.utcnow()

    db.add(payment)

    db.commit()

    db.refresh(payment)

    try:

        result = provider.create_checkout(request)

    except Exception as exc:

        payment.status = PaymentStatus.FAILED.value

        payment.failure_reason = str(exc)

        payment.updated_at = datetime.utcnow()

        db.add(payment)

        db.commit()

        raise HTTPException(

            status_code=502,

            detail="Payment provider checkout failed.",

        ) from exc

    if result.external_payment_id:

        payment.external_payment_id = (

            result.external_payment_id

        )

    if result.status != "success":

        payment.status = PaymentStatus.PENDING.value

    payment.updated_at = datetime.utcnow()

    db.add(payment)

    db.commit()

    return result