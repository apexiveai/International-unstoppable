from datetime import datetime

from decimal import Decimal

from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class PaymentStatus(str, Enum):

    PENDING = "pending"

    PROCESSING = "processing"

    PAID = "paid"

    FAILED = "failed"

    CANCELLED = "cancelled"

    REFUNDED = "refunded"

class PaymentMethod(str, Enum):

    CARD = "card"

    KBZ = "kbz"

    CB = "cb"

    AYA = "aya"

    MPU = "mpu"

    KBZPAY = "kbzpay"

    CBPAY = "cbpay"

    AYAPAY = "ayapay"

class Payment(Base):

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(

        Integer,

        primary_key=True,

    )

    tenant_id: Mapped[int] = mapped_column(

        ForeignKey("tenants.id", ondelete="CASCADE"),

        nullable=False,

        index=True,

    )

    plan_id: Mapped[int] = mapped_column(

        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),

        nullable=False,

        index=True,

    )

    subscription_id: Mapped[int | None] = mapped_column(

        ForeignKey("subscriptions.id", ondelete="SET NULL"),

        nullable=True,

        index=True,

    )

    provider: Mapped[str] = mapped_column(

        String(50),

        nullable=False,

        index=True,

    )

    payment_method: Mapped[str] = mapped_column(

        String(50),

        nullable=False,

        index=True,

    )

    status: Mapped[str] = mapped_column(

        String(30),

        nullable=False,

        default=PaymentStatus.PENDING.value,

        index=True,

    )

    amount: Mapped[Decimal] = mapped_column(

        Numeric(12, 2),

        nullable=False,

    )

    currency: Mapped[str] = mapped_column(

        String(10),

        nullable=False,

        default="USD",

    )

    checkout_reference: Mapped[str | None] = mapped_column(

        String(255),

        nullable=True,

        unique=True,

        index=True,

    )

    external_payment_id: Mapped[str | None] = mapped_column(

        String(255),

        nullable=True,

        unique=True,

        index=True,

    )

    failure_reason: Mapped[str | None] = mapped_column(

        Text,

        nullable=True,

    )

    paid_at: Mapped[datetime | None] = mapped_column(

        DateTime,

        nullable=True,

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )

    updated_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        onupdate=datetime.utcnow,

        nullable=False,

    )