from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AuditLog, Document, Execution, ExecutionEvent, User, Workflow
from app.schemas.execution import ExecutionResponse

router = APIRouter(prefix="/api/admin", tags=["Administration"])


def require_admin(user: User) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access is required.")
    return user


@router.get("/users")
def list_users(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(user)
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(user)
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(user)
    account = db.get(User, user_id)
    if account is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return db.scalars(
        select(AuditLog)
        .where(AuditLog.actor_id == account.id)
        .order_by(desc(AuditLog.created_at))
    ).all()
