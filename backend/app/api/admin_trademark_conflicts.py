import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.authorization import require_subscription_operator
from app.database import get_db
from app.models import Tenant, TrademarkConflictCheck, User

router = APIRouter(
    prefix="/api/admin/trademark-conflicts",
    tags=["Admin - Trademark Conflict"],
)


@router.get("")
def list_trademark_conflict_checks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    q: str | None = Query(default=None, min_length=1, max_length=120),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_subscription_operator),
):
    filters = []
    search_term = q.strip() if q else ""
    if search_term:
        filters.append(
            or_(
                TrademarkConflictCheck.original_filename.contains(
                    search_term, autoescape=True
                ),
                TrademarkConflictCheck.comparison_filename.contains(
                    search_term, autoescape=True
                ),
                Tenant.name.contains(search_term, autoescape=True),
                User.display_name.contains(search_term, autoescape=True),
                User.email.contains(search_term, autoescape=True),
            )
        )

    count_query = select(func.count(TrademarkConflictCheck.id))
    if filters:
        count_query = count_query.join(
            Tenant, Tenant.id == TrademarkConflictCheck.tenant_id
        ).join(User, User.id == TrademarkConflictCheck.user_id).where(*filters)
    total = db.scalar(count_query) or 0

    recent_since = datetime.utcnow() - timedelta(hours=24)
    recent_24h = db.scalar(
        select(func.count(TrademarkConflictCheck.id)).where(
            TrademarkConflictCheck.created_at >= recent_since
        )
    ) or 0
    tenants_touched = db.scalar(
        select(func.count(func.distinct(TrademarkConflictCheck.tenant_id)))
    ) or 0

    checks_query = (
        select(
            TrademarkConflictCheck,
            Tenant.name.label("tenant_name"),
            User.display_name.label("user_name"),
            User.email.label("user_email"),
        )
        .outerjoin(Tenant, Tenant.id == TrademarkConflictCheck.tenant_id)
        .outerjoin(User, User.id == TrademarkConflictCheck.user_id)
        .order_by(
            desc(TrademarkConflictCheck.created_at),
            desc(TrademarkConflictCheck.id),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    if filters:
        checks_query = checks_query.where(*filters)

    rows = db.execute(checks_query).all()
    items = []
    for check, tenant_name, user_name, user_email in rows:
        try:
            similarity_percent = json.loads(check.result_payload).get(
                "similarity_percent"
            )
        except (json.JSONDecodeError, AttributeError):
            similarity_percent = None
        items.append(
            {
                "id": check.id,
                "tenant_id": check.tenant_id,
                "tenant_name": tenant_name or f"Workspace #{check.tenant_id}",
                "user_name": user_name or "Unknown user",
                "user_email": user_email or "",
                "original_filename": check.original_filename,
                "comparison_filename": check.comparison_filename,
                "similarity_percent": similarity_percent,
                "created_at": check.created_at,
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "summary": {
            "total_checks": db.scalar(select(func.count(TrademarkConflictCheck.id))) or 0,
            "checks_last_24h": recent_24h,
            "workspaces_with_checks": tenants_touched,
        },
    }