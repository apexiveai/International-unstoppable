from __future__ import annotations

from datetime import datetime, timezone

from typing import Any

from fastapi import HTTPException, status

PRODUCTS = {

    "trademark": {

        "name": "Trademark Conflict",

        "url": "https://trademark.apexiveai.com",

    },

    "workforce": {

        "name": "Autonomous Workforce Agent",

        "url": "https://workforce.apexiveai.com",

    },

    "max_myanmar": {

        "name": "MAX-MYANMAR",

        "url": "https://max.apexiveai.com",

    },

    "mna": {

        "name": "MYANMAR NATIONAL AIRLINES",

        "url": "https://mna.apexiveai.com",

    },

}

PUBLISHED_PRODUCT_KEYS = frozenset({"trademark", "workforce"})

ACTIVE_STATUS = "ACTIVE"

VERIFIED_PAYMENT = "VERIFIED"

def utc_now() -> datetime:

    return datetime.now(timezone.utc)

def normalize(value: Any) -> str:

    return str(value or "").strip().upper()

def subscription_is_active(subscription: Any) -> bool:

    if subscription is None:

        return False

    if normalize(getattr(subscription, "status", "")) != ACTIVE_STATUS:

        return False

    expires_at = getattr(
        subscription,
        "current_period_end",
        getattr(subscription, "expires_at", None),
    )
    if expires_at is None:

        return True

    if expires_at.tzinfo is None:

        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at > utc_now()

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
    subscription_product = getattr(subscription, "product_key", None)
    if subscription_product is None:
        plan = getattr(subscription, "plan", None)
        subscription_product = getattr(plan, "product_key", None)
    return subscription_product == product_key


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

    subscription_product = getattr(subscription, "product_key", None)
    if subscription_product is None:
        plan = getattr(subscription, "plan", None)
        if plan is not None:
            subscription_product = getattr(plan, "product_key", None)

    if subscription_product != product_key:
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

        "url": product["url"],

    }