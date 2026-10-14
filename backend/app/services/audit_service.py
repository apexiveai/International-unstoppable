import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.security_audit_event import SystemAuditEvent
from app.models.tenant import TenantAuditLog


def _json_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def write_audit_log(
    db: Session,
    *,
    tenant_id: int,
    actor_user_id: int | None,
    action: str,
    target_type: str,
    target_id: int | str | None = None,
    old_value: Any = None,
    new_value: Any = None,
) -> TenantAuditLog:
    log = TenantAuditLog(
        tenant_id=tenant_id,
        actor_id=actor_user_id,
        action=action,
        entity_type=target_type,
        entity_id=str(target_id) if target_id is not None else None,
        details=json.dumps(
            {"old_value": old_value, "new_value": new_value},
            ensure_ascii=False,
            default=str,
        ),
        old_value=_json_value(old_value),
        new_value=_json_value(new_value),
    )
    db.add(log)
    return log


def write_system_audit_event(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    target_type: str,
    target_id: int | str | None = None,
    tenant_id: int | None = None,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
) -> SystemAuditEvent:
    event = SystemAuditEvent(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        outcome=outcome,
        details=json.dumps(details or {}, ensure_ascii=False, default=str),
    )
    db.add(event)
    return event
