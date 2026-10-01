from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AuditLog, Document, Tenant, User, Workflow
from app.schemas.tenant import (
    DocumentCreate,
    DocumentResponse,
    TenantResponse,
    WorkflowCreate,
    WorkflowResponse,
)

router = APIRouter(prefix="/api/tenant", tags=["Tenant"])


def require_tenant(user: User) -> int:
    if user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not assigned to a tenant.")
    return user.tenant_id


@router.get("", response_model=TenantResponse)
def current_tenant(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = require_tenant(user)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found.")
    return tenant


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = require_tenant(user)
    return db.scalars(select(Document).where(Document.tenant_id == tenant_id).order_by(desc(Document.created_at))).all()


@router.post("/documents", response_model=DocumentResponse, status_code=201)
def create_document(
    payload: DocumentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = require_tenant(user)
    document = Document(tenant_id=tenant_id, owner_id=user.id, **payload.model_dump())
    db.add(document)
    db.add(AuditLog(tenant_id=tenant_id, actor_id=user.id, action="document.created", entity_type="document"))
    db.commit()
    db.refresh(document)
    return document


@router.get("/workflows", response_model=list[WorkflowResponse])
def list_workflows(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = require_tenant(user)
    return db.scalars(select(Workflow).where(Workflow.tenant_id == tenant_id).order_by(desc(Workflow.created_at))).all()


@router.post("/workflows", response_model=WorkflowResponse, status_code=201)
def create_workflow(
    payload: WorkflowCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = require_tenant(user)
    workflow = Workflow(tenant_id=tenant_id, created_by_id=user.id, **payload.model_dump())
    db.add(workflow)
    db.add(AuditLog(tenant_id=tenant_id, actor_id=user.id, action="workflow.created", entity_type="workflow"))
    db.commit()
    db.refresh(workflow)
    return workflow


@router.get("/audit-logs")
def list_audit_logs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = require_tenant(user)
    return db.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id).order_by(desc(AuditLog.created_at))).all()
