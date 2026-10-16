from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LicensePlan(Base):
    __tablename__ = "license_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    max_robots: Mapped[int] = mapped_column(Integer, nullable=False)
    max_workflows: Mapped[int] = mapped_column(Integer, nullable=False)
    max_activations: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("license_plans.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="unassigned", index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


class LicenseActivation(Base):
    __tablename__ = "license_activations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    license_id: Mapped[int] = mapped_column(
        ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deactivated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


class LicenseEvent(Base):
    __tablename__ = "license_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    license_id: Mapped[int] = mapped_column(
        ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
