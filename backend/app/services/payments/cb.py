from __future__ import annotations

import os

from app.services.payments.base import (

    CheckoutRequest,

    CheckoutResponse,

    PaymentVerification,

)

class CBPaymentProvider:

    name = "cb_gateway"

    def __init__(self) -> None:

        self.base_url = os.getenv(

            "CB_GATEWAY_URL",

            "",

        ).rstrip("/")

        self.merchant_id = os.getenv(

            "CB_MERCHANT_ID",

            "",

        )

        self.api_key = os.getenv(

            "CB_API_KEY",

            "",

        )

        self.secret_key = os.getenv(

            "CB_SECRET_KEY",

            "",

        )

        self.checkout_url = os.getenv(

            "CB_CHECKOUT_URL",

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

                    "CB Gateway checkout URL is not configured. "

                    "Configure CB_CHECKOUT_URL after merchant "

                    "credentials and gateway specifications are provided."

                ),

            )

        # IMPORTANT:

        # Do not invent CB Bank API parameters here.

        #

        # The actual request body/signature/authentication must be

        # implemented according to the merchant integration document

        # supplied by CB Bank.

        return CheckoutResponse(

            provider=self.name,

            payment_id=request.payment_id,

            status="provider_ready",

            checkout_url=self.checkout_url,

            message=(

                "CB Gateway adapter is configured. "

                "Implement the merchant-specific request/signature "

                "according to CB Bank's integration specification."

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

                message="CB Gateway URL is not configured.",

            )

        # The actual verification API must use the merchant-specific

        # CB Bank integration specification.

        return PaymentVerification(

            verified=False,

            status="provider_verification_required",

            external_payment_id=external_payment_id,

            message=(

                "CB payment verification requires the official "

                "merchant gateway verification specification."

            ),

        )