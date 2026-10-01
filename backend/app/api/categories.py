from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import Category

from app.schemas.category import (

    CategoryCreate,

    CategoryResponse,

)

router = APIRouter(

    prefix="/api/categories",

    tags=["Categories"],

)

@router.get(

    "",

    response_model=list[CategoryResponse],

)

def get_categories(

    db: Session = Depends(get_db),

):

    return db.scalars(
        select(Category).order_by(
            Category.created_at.desc()
        ).where(Category.parent_id.is_(None))
    ).all()


@router.get(
    "/{category_slug}/children",
    response_model=list[CategoryResponse],
)
def get_category_children(
    category_slug: str,
    db: Session = Depends(get_db),
):
    category = db.scalar(select(Category).where(Category.slug == category_slug))
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db.scalars(
        select(Category)
        .where(Category.parent_id == category.id)
        .order_by(Category.created_at.asc())
    ).all()

@router.get(

    "/{category_slug}",

    response_model=CategoryResponse,

)

def get_category(

    category_slug: str,

    db: Session = Depends(get_db),

):

    category = db.scalar(

        select(Category).where(

            Category.slug == category_slug

        )

    )

    if not category:

        raise HTTPException(

            status_code=404,

            detail="Category not found",

        )

    return category

@router.post(

    "",

    response_model=CategoryResponse,

)

def create_category(

    payload: CategoryCreate,

    db: Session = Depends(get_db),

):

    existing = db.scalar(

        select(Category).where(

            Category.slug == payload.slug

        )

    )

    if existing:

        raise HTTPException(

            status_code=409,

            detail="Category already exists",

        )

    category = Category(

        **payload.model_dump()

    )

    db.add(category)

    db.commit()

    db.refresh(category)

    return category