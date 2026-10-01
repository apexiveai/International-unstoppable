from datetime import datetime

from decimal import Decimal

from pydantic import BaseModel, Field

class CreatePaymentRequest(BaseModel):

    plan_id: int = Field(gt=0)

    payment_method: str = Field(

        min_length=2,

        max_length=50,

    )

class PaymentResponse(BaseModel):

    id: int

    tenant_id: int

    plan_id: int

    subscription_id: int | None

    provider: str

    payment_method: str

    status: str

    amount: Decimal

    currency: str

    checkout_reference: str | None

    external_payment_id: str | None

    failure_reason: str | None

    paid_at: datetime | None

    created_at: datetime

    model_config = {

        "from_attributes": True,

    }

class PaymentWebhookResponse(BaseModel):

    received: bool

    payment_id: int | None = None

    status: str