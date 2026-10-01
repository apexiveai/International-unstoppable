from __future__ import annotations

from dataclasses import dataclass

from decimal import Decimal

from typing import Protocol

@dataclass

class CheckoutRequest:

    payment_id: int

    reference: str

    amount: Decimal

    currency: str

    payment_method: str

    return_url: str

    cancel_url: str

    webhook_url: str

@dataclass

class CheckoutResponse:

    provider: str

    payment_id: int

    status: str

    checkout_url: str | None = None

    external_payment_id: str | None = None

    message: str | None = None

@dataclass

class PaymentVerification:

    verified: bool

    status: str

    external_payment_id: str | None = None

    message: str | None = None

class PaymentProvider(Protocol):

    name: str

    def create_checkout(

        self,

        request: CheckoutRequest,

    ) -> CheckoutResponse:

        ...

    def verify_payment(

        self,

        external_payment_id: str,

    ) -> PaymentVerification:

        ...