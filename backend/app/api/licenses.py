import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.authorization import require_subscription_operator
from app.core.config import settings
from app.database import get_db
from app.models import License, LicenseActivation, LicenseEvent, LicensePlan, Tenant, User
from app.services.license_notifications import send_license_renewal_reminders

router = APIRouter(tags=["Licenses"])
admin_router = APIRouter(prefix="/api/admin/licenses", tags=["Admin - Licenses"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _record_event(
    db: Session,
    license_id: int,
    event_type: str,
    actor_user_id: int | None,
    details: dict | None = None,
) -> None:
    db.add(
        LicenseEvent(
            license_id=license_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            details=details or {},
        )
    )


def _license_dict(db: Session, license: License) -> dict:
    tenant = db.get(Tenant, license.tenant_id) if license.tenant_id else None
    plan = db.get(LicensePlan, license.plan_id)
    activations = db.scalars(
        select(LicenseActivation)
        .where(LicenseActivation.license_id == license.id)
        .order_by(LicenseActivation.activated_at.desc())
    ).all()
    events = db.scalars(
        select(LicenseEvent)
        .where(LicenseEvent.license_id == license.id)
        .order_by(LicenseEvent.created_at.desc())
    ).all()
    status_value = license.status
    if status_value == "active" and _as_utc(license.expires_at) <= _utcnow():
        status_value = "expired"
    return {
        "id": license.id,
        "tenant_id": license.tenant_id,
        "tenant_name": tenant.name if tenant else None,
        "plan_id": license.plan_id,
        "plan_name": plan.name if plan else None,
        "status": status_value,
        "starts_at": license.starts_at,
        "expires_at": license.expires_at,
        "price": str(license.price),
        "currency": license.currency,
        "created_at": license.created_at,
        "activations": [
            {
                "id": row.id,
                "device_id": row.device_id,
                "device_name": row.device_name,
                "activated_at": row.activated_at,
                "last_verified_at": row.last_verified_at,
                "deactivated_at": row.deactivated_at,
                "is_active": row.is_active,
            }
            for row in activations
        ],
        "events": [
            {
                "id": event.id,
                "actor_user_id": event.actor_user_id,
                "event_type": event.event_type,
                "details": event.details,
                "created_at": event.created_at,
            }
            for event in events
        ],
    }


class LicensePlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=2000)
    price: Decimal = Field(ge=0, le=1000000000)
    currency: str = Field(default="USD", min_length=3, max_length=10)
    duration_days: int = Field(gt=0, le=36500)
    max_robots: int = Field(gt=0, le=100000)
    max_workflows: int = Field(gt=0, le=100000)
    max_activations: int = Field(gt=0, le=100000)
    features: dict[str, bool] = Field(default_factory=dict)

    @field_validator("name", "currency", mode="before")
    @classmethod
    def normalize_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class LicenseCreate(BaseModel):
    plan_id: int = Field(gt=0)
    tenant_id: int | None = Field(default=None, gt=0)


class AssignCustomerRequest(BaseModel):
    tenant_id: int = Field(gt=0)


class ExtendLicenseRequest(BaseModel):
    days: int = Field(gt=0, le=36500)


class LicenseStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|suspended|revoked)$")


class LicenseValidationRequest(BaseModel):
    license_key: str = Field(min_length=20, max_length=256)
    device_id: str | None = Field(default=None, min_length=1, max_length=255)
    device_name: str | None = Field(default=None, max_length=255)
    workflow_count: int = Field(default=0, ge=0)


@admin_router.get("/plans")
def list_license_plans(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    plans = db.scalars(select(LicensePlan).order_by(LicensePlan.name)).all()
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "price": str(plan.price),
            "currency": plan.currency,
            "duration_days": plan.duration_days,
            "max_robots": plan.max_robots,
            "max_workflows": plan.max_workflows,
            "max_activations": plan.max_activations,
            "features": plan.features,
            "is_active": plan.is_active,
        }
        for plan in plans
    ]


@admin_router.post("/plans", status_code=status.HTTP_201_CREATED)
def create_license_plan(
    payload: LicensePlanCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    if db.scalar(select(LicensePlan.id).where(LicensePlan.name == payload.name)):
        raise HTTPException(status_code=409, detail="License plan name already exists.")
    plan_values = payload.model_dump()
    plan_values["currency"] = payload.currency.upper()
    plan = LicensePlan(**plan_values)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"id": plan.id, "name": plan.name, "is_active": plan.is_active}


@admin_router.get("")
def list_licenses(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    licenses = db.scalars(select(License).order_by(License.created_at.desc())).all()
    return {"items": [_license_dict(db, item) for item in licenses]}


@admin_router.post("", status_code=status.HTTP_201_CREATED)
def create_license(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    plan = db.get(LicensePlan, payload.plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=404, detail="Active license plan not found.")
    if payload.tenant_id is not None and db.get(Tenant, payload.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found.")

    now = _utcnow()
    key = f"APX-{secrets.token_urlsafe(32)}"
    license = License(
        key_hash=_hash_key(key),
        tenant_id=payload.tenant_id,
        plan_id=plan.id,
        status="active" if payload.tenant_id else "unassigned",
        starts_at=now,
        expires_at=now + timedelta(days=plan.duration_days),
        price=plan.price,
        currency=plan.currency,
        created_by_id=admin.id,
    )
    db.add(license)
    db.flush()
    _record_event(
        db,
        license.id,
        "issued",
        admin.id,
        {"plan_id": plan.id, "tenant_id": payload.tenant_id},
    )
    db.commit()
    return {"license": _license_dict(db, license), "license_key": key}


@admin_router.patch("/{license_id}/customer")
def assign_customer(
    license_id: int,
    payload: AssignCustomerRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    license = db.get(License, license_id)
    if license is None:
        raise HTTPException(status_code=404, detail="License not found.")
    if db.get(Tenant, payload.tenant_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    if _as_utc(license.expires_at) <= _utcnow():
        raise HTTPException(status_code=409, detail="An expired license must be extended first.")
    if license.status == "revoked":
        raise HTTPException(status_code=409, detail="A revoked license cannot be assigned.")
    if license.tenant_id != payload.tenant_id and db.scalar(
        select(LicenseActivation.id).where(
            LicenseActivation.license_id == license.id,
            LicenseActivation.is_active.is_(True),
        )
    ):
        raise HTTPException(
            status_code=409,
            detail="Deactivate all devices before changing the assigned customer.",
        )

    old_tenant_id = license.tenant_id
    license.tenant_id = payload.tenant_id
    if license.status == "unassigned":
        license.status = "active"
    _record_event(
        db,
        license.id,
        "customer_assigned",
        admin.id,
        {"old_tenant_id": old_tenant_id, "tenant_id": payload.tenant_id},
    )
    db.commit()
    return _license_dict(db, license)


@admin_router.post("/{license_id}/extend")
def extend_license(
    license_id: int,
    payload: ExtendLicenseRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    license = db.get(License, license_id)
    if license is None:
        raise HTTPException(status_code=404, detail="License not found.")
    if license.status == "revoked":
        raise HTTPException(status_code=409, detail="A revoked license cannot be extended.")
    previous_expiration = license.expires_at
    license.expires_at = max(_as_utc(previous_expiration), _utcnow()) + timedelta(days=payload.days)
    if license.status == "expired":
        license.status = "active"
    _record_event(
        db,
        license.id,
        "extended",
        admin.id,
        {"days": payload.days, "previous_expires_at": previous_expiration.isoformat()},
    )
    db.commit()
    return _license_dict(db, license)


@admin_router.post("/{license_id}/status")
def change_license_status(
    license_id: int,
    payload: LicenseStatusRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    license = db.get(License, license_id)
    if license is None:
        raise HTTPException(status_code=404, detail="License not found.")
    if license.status == "revoked":
        raise HTTPException(status_code=409, detail="A revoked license cannot be changed.")
    if payload.status == "active":
        plan = db.get(LicensePlan, license.plan_id)
        if license.tenant_id is None or _as_utc(license.expires_at) <= _utcnow():
            raise HTTPException(
                status_code=409,
                detail="Assign a customer and extend the license before reactivating it.",
            )
        if plan is None or not plan.is_active:
            raise HTTPException(status_code=409, detail="The license plan is inactive.")
    license.status = payload.status
    if payload.status == "revoked":
        activations = db.scalars(
            select(LicenseActivation).where(
                LicenseActivation.license_id == license.id,
                LicenseActivation.is_active.is_(True),
            )
        ).all()
        for activation in activations:
            activation.is_active = False
            activation.deactivated_at = _utcnow()
            activation.deactivated_by_id = admin.id
            _record_event(
                db,
                license.id,
                "activation_deactivated",
                admin.id,
                {"activation_id": activation.id, "reason": "license_revoked"},
            )
    _record_event(db, license.id, payload.status, admin.id)
    db.commit()
    return _license_dict(db, license)


@admin_router.post("/activations/{activation_id}/deactivate")
def deactivate_activation(
    activation_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    activation = db.get(LicenseActivation, activation_id)
    if activation is None:
        raise HTTPException(status_code=404, detail="Activation not found.")
    if activation.is_active:
        activation.is_active = False
        activation.deactivated_at = _utcnow()
        activation.deactivated_by_id = admin.id
        _record_event(
            db,
            activation.license_id,
            "activation_deactivated",
            admin.id,
            {"activation_id": activation.id, "device_id": activation.device_id},
        )
        db.commit()
    return {"id": activation.id, "is_active": activation.is_active}


@admin_router.get("/renewals")
def list_license_renewals(
    within_days: int = 30,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    if not 1 <= within_days <= 365:
        raise HTTPException(status_code=422, detail="within_days must be between 1 and 365.")
    now = _utcnow()
    cutoff = now + timedelta(days=within_days)
    licenses = db.scalars(
        select(License)
        .where(License.status == "active")
        .order_by(License.expires_at)
    ).all()
    items = [
        item for item in licenses
        if now < _as_utc(item.expires_at) <= cutoff
    ]
    return {"items": [_license_dict(db, item) for item in items]}


@admin_router.post("/renewals/send")
def send_renewal_alerts(
    db: Session = Depends(get_db),
    admin: User = Depends(require_subscription_operator),
):
    return send_license_renewal_reminders(db, actor_user_id=admin.id)


@admin_router.get("/reports")
def license_reports(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    now = _utcnow()
    licenses = db.scalars(select(License)).all()
    total = len(licenses)
    expired = sum(_as_utc(item.expires_at) <= now for item in licenses)
    active = sum(
        item.status == "active" and _as_utc(item.expires_at) > now
        for item in licenses
    )
    revenue_rows = db.execute(
        select(License.currency, func.sum(License.price), func.count(License.id))
        .where(License.status != "revoked")
        .group_by(License.currency)
    ).all()
    return {
        "total_licenses": total,
        "active_licenses": active,
        "expired_licenses": expired,
        "issued_value_by_currency": [
            {"currency": currency, "amount": str(amount or Decimal("0")), "licenses": count}
            for currency, amount, count in revenue_rows
        ],
    }


@router.post("/api/licenses/validate")
def validate_license(
    payload: LicenseValidationRequest,
    x_rpa_service_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    configured_token = settings.rpa_license_service_token
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RPA license verification is not configured.",
        )
    if not x_rpa_service_token or not hmac.compare_digest(
        x_rpa_service_token, configured_token
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")

    license = db.scalar(
        select(License)
        .where(License.key_hash == _hash_key(payload.license_key))
        .with_for_update()
    )
    if license is None:
        raise HTTPException(status_code=403, detail="Invalid license.")
    now = _utcnow()
    if license.status != "active":
        raise HTTPException(status_code=403, detail=f"License is {license.status}.")
    if license.tenant_id is None or db.get(Tenant, license.tenant_id) is None:
        raise HTTPException(status_code=403, detail="License is not assigned to a customer.")
    if _as_utc(license.starts_at) > now or _as_utc(license.expires_at) <= now:
        raise HTTPException(status_code=403, detail="License is not within its valid term.")

    plan = db.get(LicensePlan, license.plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=403, detail="License plan is inactive.")
    if payload.workflow_count > plan.max_workflows:
        raise HTTPException(status_code=403, detail="License workflow limit exceeded.")

    if payload.device_id:
        activation = db.scalar(
            select(LicenseActivation)
            .where(
                LicenseActivation.license_id == license.id,
                LicenseActivation.device_id == payload.device_id,
                LicenseActivation.is_active.is_(True),
            )
            .with_for_update()
        )
        if activation is None:
            active_count = db.scalar(
                select(func.count(LicenseActivation.id)).where(
                    LicenseActivation.license_id == license.id,
                    LicenseActivation.is_active.is_(True),
                )
            ) or 0
            activation_limit = min(plan.max_robots, plan.max_activations)
            if active_count >= activation_limit:
                raise HTTPException(status_code=403, detail="License activation limit reached.")
            activation = LicenseActivation(
                license_id=license.id,
                device_id=payload.device_id,
                device_name=payload.device_name or payload.device_id,
                activated_at=now,
                last_verified_at=now,
                is_active=True,
            )
            db.add(activation)
            _record_event(
                db,
                license.id,
                "activated",
                None,
                {"device_id": payload.device_id, "device_name": payload.device_name},
            )
        else:
            activation.last_verified_at = now
            if payload.device_name:
                activation.device_name = payload.device_name
    db.commit()
    return {
        "valid": True,
        "license_id": license.id,
        "tenant_id": license.tenant_id,
        "expires_at": license.expires_at,
        "max_robots": plan.max_robots,
        "max_workflows": plan.max_workflows,
        "max_activations": plan.max_activations,
        "features": plan.features,
    }


router.include_router(admin_router)
