from math import ceil
from typing import Any

from fastapi import Query
from sqlalchemy import func, select
from pydantic import BaseModel
from sqlalchemy.orm import Session


class Pagination(BaseModel):
    page: int
    page_size: int


def pagination_parameters(
    page: int = Query(default=1, ge=1, le=100),
    page_size: int = Query(default=10, ge=1, le=100),
) -> Pagination:
    return Pagination(page=page, page_size=page_size)


def paginate_statement(
    db: Session,
    statement: Any,
    *,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )
    total = db.scalar(count_statement) or 0
    items = db.scalars(
        statement.order_by(None)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": min(100, ceil(total / page_size)) if total else 0,
    }
