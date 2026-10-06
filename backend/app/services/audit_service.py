import json
from typing import Any

from sqlalchemy.orm import Session

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
