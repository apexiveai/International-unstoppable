from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import desc, select

from sqlalchemy.orm import Session

from app.auth import get_current_user

from app.database import get_db

from app.models import Resource, User

from app.schemas.resource import ResourceCreate, ResourceResponse

router = APIRouter(

    prefix="/api/resources",

    tags=["Resources"],

)

@router.get(

    "",

    response_model=list[ResourceResponse],

)

def list_resources(

    db: Session = Depends(get_db),

):

    resources = db.scalars(

        select(Resource)

        .where(Resource.is_published.is_(True))

        .order_by(desc(Resource.created_at))

    ).all()

    return resources

@router.get(

    "/featured",

    response_model=list[ResourceResponse],

)

def featured_resources(

    db: Session = Depends(get_db),

):

    resources = db.scalars(

        select(Resource)

        .where(

            Resource.is_published.is_(True),

            Resource.is_featured.is_(True),

        )

        .order_by(desc(Resource.created_at))

    ).all()

    return resources

@router.get(

    "/{slug}",

    response_model=ResourceResponse,

)

def get_resource(

    slug: str,

    db: Session = Depends(get_db),

):

    resource = db.scalar(

        select(Resource).where(

            Resource.slug == slug,

            Resource.is_published.is_(True),

        )

    )

    if not resource:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,

            detail="Resource not found",

        )

    resource.downloads += 1

    db.commit()

    db.refresh(resource)

    return resource

@router.post(

    "",

    response_model=ResourceResponse,

    status_code=status.HTTP_201_CREATED,

)

def create_resource(

    payload: ResourceCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    existing = db.scalar(

        select(Resource).where(

            Resource.slug == payload.slug,

        )

    )

    if existing:

        raise HTTPException(

            status_code=status.HTTP_409_CONFLICT,

            detail="Resource slug already exists",

        )

    is_featured = payload.is_featured if current_user.is_admin else False
    is_published = payload.is_published if current_user.is_admin else False
    resource = Resource(
        title=payload.title,

        slug=payload.slug,

        description=payload.description,

        content=payload.content,

        resource_type=payload.resource_type,

        category=payload.category,

        author_id=current_user.id,

        file_url=payload.file_url,

        file_size=payload.file_size,

        is_featured=is_featured,

        is_published=is_published,

    )

    db.add(resource)

    db.commit()

    db.refresh(resource)

    return resource