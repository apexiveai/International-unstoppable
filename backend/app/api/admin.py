from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.auth import generate_temporary_password, hash_password
from app.core.authorization import require_admin as require_authenticated_admin
from app.database import get_db
from app.models import (
    AuditLog,
    Document,
    Execution,
    ExecutionEvent,
    SubscriptionPlan,
    User,
    Workflow,
)
from app.schemas.execution import ExecutionResponse

router = APIRouter(prefix="/api/admin", tags=["Administration"])


class AdminCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=100)

    @field_validator("username", "display_name", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class AdminStatusRequest(BaseModel):
    is_active: bool


class PlanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    monthly_price: Decimal | None = Field(default=None, ge=0, le=100000000)
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    billing_cycle: str | None = Field(default=None, min_length=2, max_length=30)
    is_active: bool | None = None

    @field_validator("*", mode="before")
    @classmethod
    def reject_null_fields(cls, value):
        if value is None:
            raise ValueError("Null values are not allowed.")
        return value

    @field_validator("name", "currency", "billing_cycle", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Values cannot be blank.")
        return value

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("billing_cycle", mode="before")
    @classmethod
    def normalize_billing_cycle(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


def _serialize_admin(account: User) -> dict:
    return {
        "id": account.id,
        "username": account.username,
        "display_name": account.display_name,
        "email": account.email,
        "is_active": account.is_active,
        "is_admin": account.is_admin,
        "created_at": account.created_at,
    }


@router.get("/accounts")
def list_admin_accounts(
    _admin: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    accounts = db.scalars(
        select(User)
        .where(User.is_admin.is_(True))
        .order_by(User.created_at.desc())
    ).all()
    return [_serialize_admin(account) for account in accounts]


@router.get("/accounts/{account_id}")
def get_admin_account(
    account_id: int,
    _admin: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    account = db.get(User, account_id)
    if account is None or not account.is_admin:
        raise HTTPException(status_code=404, detail="Admin account not found.")
    return _serialize_admin(account)


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_admin_account(
    payload: AdminCreateRequest,
    admin: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    username = payload.username.strip()
    email = str(payload.email).strip().lower()
    duplicate = db.scalar(
        select(User.id).where((User.username == username) | (User.email == email))
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists.",
        )
    temporary_password = generate_temporary_password()
    account = User(
        username=username,
        email=email,
        password_hash=hash_password(temporary_password),
        display_name=payload.display_name.strip(),
        tenant_id=admin.tenant_id,
        is_active=True,
        is_admin=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return {
        "admin": _serialize_admin(account),
        "temporary_password": temporary_password,
    }


@router.patch("/accounts/{account_id}/status")
def change_admin_status(
    account_id: int,
    payload: AdminStatusRequest,
    admin: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    account = db.get(User, account_id)
    if account is None or not account.is_admin:
        raise HTTPException(status_code=404, detail="Admin account not found.")
    if not payload.is_active:
        if account.id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You cannot disable your own administrator account.",
            )
        active_admins = db.scalar(
            select(func.count(User.id)).where(
                User.is_admin.is_(True),
                User.is_active.is_(True),
            )
        )
        if active_admins is not None and active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last active administrator cannot be disabled.",
            )
    account.is_active = payload.is_active
    db.commit()
    db.refresh(account)
    return _serialize_admin(account)


@router.get("/settings/plans")
def list_admin_plan_settings(
    _admin: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    plans = db.scalars(select(SubscriptionPlan).order_by(SubscriptionPlan.id)).all()
    return [
        {
            "id": plan.id,
            "product_key": plan.product_key,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": str(plan.monthly_price),
            "currency": plan.currency,
            "billing_cycle": plan.billing_cycle,
            "is_active": plan.is_active,
        }
        for plan in plans
    ]


@router.patch("/settings/plans/{plan_id}")
def update_admin_plan_settings(
    plan_id: int,
    payload: PlanUpdateRequest,
    _admin: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    plan = db.get(SubscriptionPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found.")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "currency":
            value = value.strip().upper()
        elif field == "billing_cycle":
            value = value.strip().lower()
        elif isinstance(value, str):
            value = value.strip()
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return {
        "id": plan.id,
        "product_key": plan.product_key,
        "name": plan.name,
        "description": plan.description,
        "monthly_price": str(plan.monthly_price),
        "currency": plan.currency,
        "billing_cycle": plan.billing_cycle,
        "is_active": plan.is_active,
    }


@router.get("/users")
def list_users(
    user: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    result = []
    for account in users:
        result.append({
            "id": account.id,
            "username": account.username,
            "display_name": account.display_name,
            "email": account.email,
            "tenant_id": account.tenant_id,
            "is_active": account.is_active,
            "created_at": account.created_at,
            "documents": db.query(Document).filter(Document.owner_id == account.id).count(),
            "workflows": db.query(Workflow).filter(Workflow.created_by_id == account.id).count(),
            "executions": db.query(Execution).filter(Execution.requested_by_id == account.id).count(),
        })
    return result


@router.get("/users/{user_id}/history", response_model=list[ExecutionResponse])
def user_execution_history(
    user_id: int,
    user: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    account = db.get(User, user_id)
    if account is None:
        raise HTTPException(status_code=404, detail="User not found.")
    executions = db.scalars(
        select(Execution)
        .where(Execution.requested_by_id == account.id)
        .order_by(desc(Execution.created_at))
    ).all()
    for execution in executions:
        execution.events = list(db.scalars(
            select(ExecutionEvent)
            .where(ExecutionEvent.execution_id == execution.id)
            .order_by(ExecutionEvent.created_at)
        ).all())
    return executions


@router.get("/users/{user_id}/audit-logs")
def user_audit_history(
    user_id: int,
    user: User = Depends(require_authenticated_admin),
    db: Session = Depends(get_db),
):
    account = db.get(User, user_id)
    if account is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return db.scalars(
        select(AuditLog)
        .where(AuditLog.actor_id == account.id)
        .order_by(desc(AuditLog.created_at))
    ).all()
