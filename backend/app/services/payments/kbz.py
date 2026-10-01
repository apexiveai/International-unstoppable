from __future__ import annotations

import os

from app.services.payments.base import (

    CheckoutRequest,

    CheckoutResponse,

    PaymentVerification,

)

class KBZPaymentProvider:

    name = "kbzpay"

    def __init__(self) -> None:

        self.base_url = os.getenv(

            "KBZPAY_GATEWAY_URL",

            "",

        ).rstrip("/")

        self.merchant_id = os.getenv(

            "KBZPAY_MERCHANT_ID",

            "",

        )

        self.api_key = os.getenv(

            "KBZPAY_API_KEY",

            "",

        )

        self.secret_key = os.getenv(

            "KBZPAY_SECRET_KEY",

            "",

        )

        self.checkout_url = os.getenv(

            "KBZPAY_CHECKOUT_URL",

            "",

        )

    def create_checkout(

        self,

        request: CheckoutRequest,

    ) -> CheckoutResponse:

        if not self.checkout_url:

            return CheckoutResponse(

                provider=self.name,

                payment_id=request.payment_id,

                status="configuration_required",

                message=(

                    "KBZPay gateway checkout URL is not configured."

                ),

            )

        return CheckoutResponse(

            provider=self.name,

            payment_id=request.payment_id,

            status="provider_ready",

            checkout_url=self.checkout_url,

            message=(

                "KBZPay adapter is ready for official merchant "

                "gateway integration."

            ),

        )

    def verify_payment(

        self,

        external_payment_id: str,

    ) -> PaymentVerification:

        if not self.base_url:

            return PaymentVerification(

                verified=False,

                status="configuration_required",

                external_payment_id=external_payment_id,

                message="KBZPay gateway URL is not configured.",

            )

        return PaymentVerification(

            verified=False,

            status="provider_verification_required",

            external_payment_id=external_payment_id,

            message=(

                "KBZPay payment verification requires the official "

                "merchant integration specification."

            ),

        )