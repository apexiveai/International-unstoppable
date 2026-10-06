from __future__ import annotations

from datetime import datetime, timezone

from enum import Enum

class ProductKey(str, Enum):

    TRADEMARK = "trademark"

    WORKFORCE = "workforce"

    MAX_MYANMAR = "max_myanmar"

    MNA = "mna"

class SubscriptionStatus(str, Enum):

    PENDING = "PENDING"

    ACTIVE = "ACTIVE"

    EXPIRED = "EXPIRED"

    SUSPENDED = "SUSPENDED"

    CANCELLED = "CANCELLED"

class PaymentStatus(str, Enum):

    PENDING = "PENDING"

    VERIFIED = "VERIFIED"

    REJECTED = "REJECTED"

    REFUNDED = "REFUNDED"

PRODUCTS = {

    ProductKey.TRADEMARK: {

        "key": "trademark",

        "name": "Trademark Conflict",

    },

    ProductKey.WORKFORCE: {

        "key": "workforce",

        "name": "Autonomous Workforce Agent",

    },

    ProductKey.MAX_MYANMAR: {

        "key": "max_myanmar",

        "name": "MAX-MYANMAR",

    },

    ProductKey.MNA: {

        "key": "mna",

        "name": "MYANMAR NATIONAL AIRLINES",

    },

}

def utc_now() -> datetime:

    return datetime.now(timezone.utc)

def is_subscription_active(subscription) -> bool:

    """

    Central subscription entitlement check.

    This is the single rule that product APIs should use.

    """

    if subscription is None:

        return False

    status = str(

        getattr(subscription, "status", "")

    ).upper()

    if status != SubscriptionStatus.ACTIVE.value:

        return False

    expires_at = getattr(

        subscription,

        "expires_at",

        None,

    )

    if expires_at is None:

        return True

    now = utc_now()

    # Handle naive DB datetime safely.

    if expires_at.tzinfo is None:

        expires_at = expires_at.replace(

            tzinfo=timezone.utc

        )

    if expires_at <= now:

        return False

    return True

def payment_allows_activation(payment) -> bool:

    """

    Payment MUST be verified before subscription activation.

    """

    if payment is None:

        return False

    status = str(

        getattr(payment, "status", "")

    ).upper()

    return (

        status

        == PaymentStatus.VERIFIED.value

    )

def can_access_product(

    subscription,

    product_key: str,

) -> bool:

    """

    Verify that the subscription belongs to

    the requested product and is active.

    """

    normalized = str(

        product_key

    ).lower().strip()

    valid_products = {

        item.value

        for item in ProductKey

    }

    if normalized not in valid_products:

        return False

    subscription_product = getattr(

        subscription,

        "product_key",

        None,

    )

    if subscription_product is None:

        plan = getattr(

            subscription,

            "plan",

            None,

        )

        if plan is not None:

            subscription_product = getattr(

                plan,

                "product_key",

                None,

            )

    if subscription_product is None:

        return False

    if str(

        subscription_product

    ).lower().strip() != normalized:

        return False

    return is_subscription_active(

        subscription

    )

def require_verified_payment(payment):

    """

    Raise a normal Python error when an admin attempts

    to activate a subscription before payment verification.

    """

    if not payment_allows_activation(

        payment

    ):

        raise ValueError(

            "Payment must be verified before activation."

        )

def activate_subscription(

    subscription,

    payment,

    admin_id: int,

    starts_at: datetime | None = None,

):

    """

    Central activation rule.

    IMPORTANT:

    This function deliberately refuses to activate

    an unverified payment.

    """

    require_verified_payment(payment)

    if starts_at is None:

        starts_at = utc_now()

    subscription.status = (

        SubscriptionStatus.ACTIVE.value

    )

    subscription.starts_at = starts_at

    if hasattr(

        subscription,

        "activated_by",

    ):
        subscription.activated_by = admin_id

    if hasattr(

        subscription,

        "activated_at",

    ):

        subscription.activated_at = utc_now()

    if hasattr(

        subscription,

        "suspended_at",

    ):

        subscription.suspended_at = None

    return subscription

def suspend_subscription(

    subscription,

):

    subscription.status = (

        SubscriptionStatus.SUSPENDED.value

    )

    if hasattr(

        subscription,

        "suspended_at",

    ):

        subscription.suspended_at = utc_now()

    return subscription

def cancel_subscription(

    subscription,

):

    subscription.status = (

        SubscriptionStatus.CANCELLED.value

    )

    return subscription

def expire_subscription(

    subscription,

):

    subscription.status = (

        SubscriptionStatus.EXPIRED.value

    )

    return subscription