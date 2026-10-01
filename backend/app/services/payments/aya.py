from __future__ import annotations

import os

from app.services.payments.base import (

    CheckoutRequest,

    CheckoutResponse,

    PaymentVerification,

)

class AYAPaymentProvider:

    name = "ayapay"

    def __init__(self) -> None:

        self.base_url = os.getenv(

            "AYAPAY_GATEWAY_URL",

            "",

        ).rstrip("/")

        self.merchant_id = os.getenv(

            "AYAPAY_MERCHANT_ID",

            "",

        )

        self.api_key = os.getenv(

            "AYAPAY_API_KEY",

            "",

        )

        self.secret_key = os.getenv(

            "AYAPAY_SECRET_KEY",

            "",

        )

        self.checkout_url = os.getenv(

            "AYAPAY_CHECKOUT_URL",

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

                    "AYA Pay gateway checkout URL is not configured."

                ),

            )

        return CheckoutResponse(

            provider=self.name,

            payment_id=request.payment_id,

            status="provider_ready",

            checkout_url=self.checkout_url,

            message=(

                "AYA Pay adapter is ready for official merchant "

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

                message="AYA Pay gateway URL is not configured.",

            )

        return PaymentVerification(

            verified=False,

            status="provider_verification_required",

            external_payment_id=external_payment_id,

            message=(

                "AYA Pay payment verification requires the official "

                "merchant integration specification."

            ),

        )