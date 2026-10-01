from datetime import datetime

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class SubscriptionPlanResponse(BaseModel):

    id: int

    product_key: str

    name: str

    description: str

    monthly_price: Decimal

    currency: str

    billing_cycle: str

    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class SubscribeRequest(BaseModel):

    plan_id: int = Field(gt=0)

class SubscriptionResponse(BaseModel):

    id: int

    tenant_id: int

    plan_id: int

    status: str

    price: Decimal

    currency: str

    billing_cycle: str

    start_date: datetime

    current_period_end: datetime | None

    cancelled_at: datetime | None

    external_subscription_id: str | None

    plan: SubscriptionPlanResponse

    model_config = ConfigDict(from_attributes=True)

class SubscriptionAccessResponse(BaseModel):

    product_key: str

    has_access: bool

    subscription_id: int | None = None

    status: str | None = None

    current_period_end: datetime | None = None

class SubscriptionCancelResponse(BaseModel):

    id: int

    status: str

    cancelled_at: datetime