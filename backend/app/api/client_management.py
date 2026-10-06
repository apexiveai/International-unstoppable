from __future__ import annotations

import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import generate_temporary_password, hash_password
from app.core.authorization import require_admin
from app.database import get_db
from app.models import Tenant, User
from app.services.audit_service import write_audit_log

router = APIRouter(prefix="/api/admin/clients", tags=["Admin - Clients"])


class ClientCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=100)
    company_name: str | None = Field(default=None, max_length=200)


class ClientUpdateRequest(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    company_name: str | None = Field(default=None, min_length=1, max_length=200)


class ClientStatusRequest(BaseModel):
    is_active: bool


class ClientPasswordResetResponse(BaseModel):
    user_id: int
    username: str
    temporary_password: str


def _serialize_client(user: User, company_name: str | None = None) -> dict:
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "company_name": company_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at,
    }


def _client_or_404(db: Session, client_id: int) -> User:
    client = db.get(User, client_id)
    if client is None or client.is_admin:
        raise HTTPException(status_code=404, detail="Client not found.")
    return client


def _ensure_tenant(db: Session, client: User) -> Tenant:
    tenant = db.get(Tenant, client.tenant_id) if client.tenant_id else None
    if tenant is None:
        tenant = Tenant(
            name=f"{client.display_name} Workspace",
            slug=f"client-{client.id}-workspace",
        )
        db.add(tenant)
        db.flush()
        client.tenant_id = tenant.id
    return tenant


@router.get("")
def list_clients(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    rows = db.execute(
        select(User, Tenant.name)
        .outerjoin(Tenant, Tenant.id == User.tenant_id)
        .where(User.is_admin.is_(False))
        .order_by(User.created_at.desc())
    ).all()
    clients = [_serialize_client(user, company) for user, company in rows]
    return {"count": len(clients), "clients": clients}


@router.get("/{client_id}")
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    client = _client_or_404(db, client_id)
    company_name = (
        db.scalar(select(Tenant.name).where(Tenant.id == client.tenant_id))
        if client.tenant_id is not None
        else None
    )
    return _serialize_client(client, company_name)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    username = payload.username.strip()
    email = str(payload.email).strip().lower()
    duplicate = db.scalar(
        select(User).where(
            (User.username == username) | (User.email == email)
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists.",
        )

    tenant_name = (payload.company_name or "").strip() or payload.display_name.strip()
    slug = f"{username.lower()}-{secrets.token_hex(4)}-workspace"
    tenant = Tenant(name=tenant_name, slug=slug)
    db.add(tenant)
    db.flush()
    temporary_password = generate_temporary_password()
    client = User(
        username=username,
        email=email,
        password_hash=hash_password(temporary_password),
        display_name=payload.display_name.strip(),
        tenant_id=tenant.id,
        is_active=True,
        is_admin=False,
    )
    db.add(client)
    db.flush()
    write_audit_log(
        db,
        tenant_id=tenant.id,
        actor_user_id=admin.id,
        action="client.created",
        target_type="user",
        target_id=client.id,
        new_value={"username": username, "email": email, "tenant": tenant_name},
    )
    db.commit()
    db.refresh(client)
    return {
        "client": _serialize_client(client, tenant_name),
        "temporary_password": temporary_password,
    }


@router.patch("/{client_id}")
def update_client(
    client_id: int,
    payload: ClientUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    client = _client_or_404(db, client_id)
    tenant = _ensure_tenant(db, client)
    old_value = {
        "email": client.email,
        "display_name": client.display_name,
    }
    if payload.email is not None:
        email = str(payload.email).strip().lower()
        duplicate = db.scalar(
            select(User).where(User.email == email, User.id != client.id)
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already belongs to another account.",
            )
        client.email = email
        client.email_verified_at = None
    if payload.display_name is not None:
        client.display_name = payload.display_name.strip()
    if payload.company_name is not None:
        tenant.name = payload.company_name.strip()

    write_audit_log(
        db,
        tenant_id=tenant.id,
        actor_user_id=admin.id,
        action="client.updated",
        target_type="user",
        target_id=client.id,
        old_value=old_value,
        new_value={
            "email": client.email,
            "display_name": client.display_name,
        },
    )
    db.commit()
    db.refresh(client)
    return {"client": _serialize_client(client, tenant.name)}


@router.patch("/{client_id}/status")
def change_client_status(
    client_id: int,
    payload: ClientStatusRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    client = _client_or_404(db, client_id)
    tenant = _ensure_tenant(db, client)
    previous_status = client.is_active
    client.is_active = payload.is_active
    write_audit_log(
        db,
        tenant_id=tenant.id,
        actor_user_id=admin.id,
        action="client.enabled" if payload.is_active else "client.disabled",
        target_type="user",
        target_id=client.id,
        old_value={"is_active": previous_status},
        new_value={"is_active": payload.is_active},
    )
    db.commit()
    return {"client": _serialize_client(client)}


@router.post(
    "/{client_id}/reset-password",
    response_model=ClientPasswordResetResponse,
)
def reset_client_password(
    client_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    client = _client_or_404(db, client_id)
    tenant = _ensure_tenant(db, client)
    temporary_password = generate_temporary_password()
    client.password_hash = hash_password(temporary_password)
    write_audit_log(
        db,
        tenant_id=tenant.id,
        actor_user_id=admin.id,
        action="client.password_reset",
        target_type="user",
        target_id=client.id,
        new_value={"password_reset": True},
    )
    db.commit()
    return {
        "user_id": client.id,
        "username": client.username,
        "temporary_password": temporary_password,
    }


@router.delete("/{client_id}")
def disable_client(
    client_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    client = _client_or_404(db, client_id)
    tenant = _ensure_tenant(db, client)
    client.is_active = False
    write_audit_log(
        db,
        tenant_id=tenant.id,
        actor_user_id=admin.id,
        action="client.disabled",
        target_type="user",
        target_id=client.id,
        old_value={"is_active": True},
        new_value={"is_active": False},
    )
    db.commit()
    return {"message": "Client disabled.", "client_id": client.id}
