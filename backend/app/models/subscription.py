from datetime import datetime

from sqlalchemy import (

    DateTime,

    ForeignKey,

    Integer,

    Numeric,

    String,

    Text,

    Boolean,

)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class SubscriptionPlan(Base):

    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    product_key: Mapped[str] = mapped_column(

        String(100),

        unique=True,

        nullable=False,

        index=True,

    )

    name: Mapped[str] = mapped_column(

        String(200),

        nullable=False,

    )

    description: Mapped[str] = mapped_column(

        Text,

        nullable=False,

        default="",

    )

    monthly_price: Mapped[float] = mapped_column(

        Numeric(12, 2),

        nullable=False,

    )

    currency: Mapped[str] = mapped_column(

        String(10),

        nullable=False,

        default="USD",

    )

    billing_cycle: Mapped[str] = mapped_column(

        String(30),

        nullable=False,

        default="monthly",

    )

    is_active: Mapped[bool] = mapped_column(

        Boolean,

        nullable=False,

        default=True,

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )

    subscriptions = relationship(

        "Subscription",

        back_populates="plan",

    )

class Subscription(Base):

    __tablename__ = "subscriptions"

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

    status: Mapped[str] = mapped_column(

        String(30),

        nullable=False,

        default="active",

        index=True,

    )

    price: Mapped[float] = mapped_column(

        Numeric(12, 2),

        nullable=False,

    )

    currency: Mapped[str] = mapped_column(

        String(10),

        nullable=False,

        default="USD",

    )

    billing_cycle: Mapped[str] = mapped_column(

        String(30),

        nullable=False,

        default="monthly",

    )

    start_date: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )

    current_period_end: Mapped[datetime | None] = mapped_column(

        DateTime,

        nullable=True,

    )

    cancelled_at: Mapped[datetime | None] = mapped_column(

        DateTime,

        nullable=True,

    )

    external_subscription_id: Mapped[str | None] = mapped_column(

        String(255),

        nullable=True,

        index=True,

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

    plan = relationship(

        "SubscriptionPlan",

        back_populates="subscriptions",

    )

class BillingEvent(Base):

    __tablename__ = "billing_events"

    id: Mapped[int] = mapped_column(

        Integer,

        primary_key=True,

    )

    tenant_id: Mapped[int] = mapped_column(

        ForeignKey("tenants.id", ondelete="CASCADE"),

        nullable=False,

        index=True,

    )

    subscription_id: Mapped[int | None] = mapped_column(

        ForeignKey("subscriptions.id", ondelete="SET NULL"),

        nullable=True,

        index=True,

    )

    event_type: Mapped[str] = mapped_column(

        String(100),

        nullable=False,

        index=True,

    )

    status: Mapped[str] = mapped_column(

        String(50),

        nullable=False,

        default="received",

    )
    external_event_id: Mapped[str | None] = mapped_column(

        String(255),

        nullable=True,

        unique=True,

        index=True,

    )

    amount: Mapped[float | None] = mapped_column(

        Numeric(12, 2),

        nullable=True,

    )

    currency: Mapped[str] = mapped_column(

        String(10),

        nullable=False,

        default="USD",

    )

    details: Mapped[str] = mapped_column(

        Text,

        nullable=False,

        default="",

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )