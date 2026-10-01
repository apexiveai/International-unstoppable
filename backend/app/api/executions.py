import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import AuditLog, Execution, ExecutionEvent, User
from app.schemas.execution import ApprovalDecision, ExecutionCreate, ExecutionResponse

router = APIRouter(prefix="/executions", tags=["Executions"])


def tenant_id_for(user: User) -> int:
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant.")
    return user.tenant_id


def record(db: Session, execution: Execution, user: User | None, event_type: str, status_value: str, details: dict) -> None:
    db.add(ExecutionEvent(
        execution_id=execution.id,
        tenant_id=execution.tenant_id,
        actor_id=user.id if user else None,
        event_type=event_type,
        status=status_value,
        details=json.dumps(details),
    ))
    db.add(AuditLog(
        tenant_id=execution.tenant_id,
        actor_id=user.id if user else None,
        action=f"execution.{event_type}",
        entity_type="execution",
        entity_id=str(execution.id),
        details=json.dumps(details),
    ))


def get_execution(execution_id: int, user: User, db: Session) -> Execution:
    execution = db.scalar(select(Execution).where(
        Execution.id == execution_id,
        Execution.tenant_id == tenant_id_for(user),
    ))
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found.")
    return execution


@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
def create_execution(payload: ExecutionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    execution = Execution(
        tenant_id=tenant_id_for(user),
        requested_by_id=user.id,
        workflow_name=payload.workflow_name,
        input_payload=json.dumps(payload.input_payload),
    )
    db.add(execution)
    db.flush()
    record(db, execution, user, "submitted", "queued", {"message": "Execution accepted by the API."})
    db.commit()
    db.refresh(execution)
    execution.events = list(db.scalars(select(ExecutionEvent).where(ExecutionEvent.execution_id == execution.id).order_by(ExecutionEvent.created_at)).all())
    return execution


@router.get("", response_model=list[ExecutionResponse])
def list_executions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    executions = db.scalars(select(Execution).where(
        Execution.tenant_id == tenant_id_for(user),
        Execution.requested_by_id == user.id,
    ).order_by(desc(Execution.created_at))).all()
    for execution in executions:
        execution.events = list(db.scalars(select(ExecutionEvent).where(ExecutionEvent.execution_id == execution.id).order_by(ExecutionEvent.created_at)).all())
    return executions


@router.get("/{execution_id}", response_model=ExecutionResponse)
def read_execution(execution_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    execution = get_execution(execution_id, user, db)
    execution.events = list(db.scalars(select(ExecutionEvent).where(ExecutionEvent.execution_id == execution.id).order_by(ExecutionEvent.created_at)).all())
    return execution


@router.post("/{execution_id}/claim", response_model=ExecutionResponse)
def claim_execution(execution_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    execution = get_execution(execution_id, user, db)
    if execution.status != "queued":
        raise HTTPException(status_code=409, detail="Only queued executions can be claimed.")
    execution.status = "planning"
    execution.current_step = "supervisor_planning"
    record(db, execution, user, "worker.claimed", execution.status, {"worker": "AEWE"})
    record(db, execution, user, "supervisor.planning", execution.status, {"checkpoint": "pending"})
    execution.checkpoint = json.dumps({"graph_node": "supervisor_planning", "resume_token": f"execution-{execution.id}-v{execution.version}"})
    db.commit()
    return read_execution(execution_id, user, db)


@router.post("/{execution_id}/agent", response_model=ExecutionResponse)
def run_agent(execution_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    execution = get_execution(execution_id, user, db)
    if execution.status not in {"planning", "resuming"}:
        raise HTTPException(status_code=409, detail="Execution is not ready for agent execution.")
    execution.status = "awaiting_approval"
    execution.current_step = "approval_gate"
    record(db, execution, user, "agent.executed", execution.status, {"checkpoint": execution.checkpoint})
    record(db, execution, user, "approval.required", execution.status, {"reason": "Human approval is required before external side effects."})
    db.commit()
    return read_execution(execution_id, user, db)


@router.post("/{execution_id}/approval", response_model=ExecutionResponse)
def decide_approval(execution_id: int, payload: ApprovalDecision, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    execution = get_execution(execution_id, user, db)
    if execution.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Execution is not waiting for approval.")
    execution.status = "resuming" if payload.approved else "rejected"
    execution.current_step = "resume_agent_execution" if payload.approved else "approval_gate"
    record(db, execution, user, "approval.granted" if payload.approved else "approval.rejected", execution.status, {"comment": payload.comment})
    db.commit()
    return read_execution(execution_id, user, db)


@router.post("/{execution_id}/verify", response_model=ExecutionResponse)
def verify_execution(execution_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    execution = get_execution(execution_id, user, db)
    if execution.status != "resuming":
        raise HTTPException(status_code=409, detail="Execution must be resumed before verification.")
    execution.status = "completed"
    execution.current_step = "workflow_completed"
    execution.result_payload = json.dumps({"verified": True, "message": "Workflow completed successfully."})
    record(db, execution, user, "verification.completed", execution.status, {"verified": True})
    record(db, execution, user, "workflow.completed", execution.status, {})
    db.commit()
    return read_execution(execution_id, user, db)
