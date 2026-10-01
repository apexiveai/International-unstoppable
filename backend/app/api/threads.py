import re

import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select

from sqlalchemy.orm import Session

from app.auth import get_current_user

from app.database import get_db

from app.models import Category, Thread, User

from app.schemas.thread import ThreadCreate, ThreadResponse

router = APIRouter(

    prefix="/api/threads",

    tags=["Threads"],

)

def generate_slug(title: str) -> str:

    """

    Convert thread title into a URL-safe slug.

    """

    value = unicodedata.normalize("NFKD", title)

    value = value.encode("ascii", "ignore").decode("ascii")

    value = value.lower()

    value = re.sub(r"[^a-z0-9\s-]", "", value)

    value = re.sub(r"[\s_-]+", "-", value)

    value = re.sub(r"^-+|-+$", "", value)

    return value[:300]

def generate_unique_slug(

    db: Session,

    title: str,

) -> str:

    """

    Generate a unique thread slug.

    Example:

        my-first-thread

        my-first-thread-2

        my-first-thread-3

    """

    base_slug = generate_slug(title)

    if not base_slug:

        base_slug = "discussion"

    slug = base_slug

    counter = 2

    while db.scalar(

        select(Thread).where(Thread.slug == slug)

    ):

        slug = f"{base_slug}-{counter}"

        counter += 1

    return slug

@router.get(

    "",

    response_model=list[ThreadResponse],

)

def get_threads(

    category_id: int | None = Query(default=None),

    db: Session = Depends(get_db),

):

    """

    Get threads.

    Optional:

        ?category_id=1

    """

    query = select(Thread)

    if category_id is not None:

        query = query.where(

            Thread.category_id == category_id

        )

    query = query.order_by(

        Thread.created_at.desc()

    )

    return db.scalars(query).all()

@router.get(

    "/by-slug/{category_slug}/{thread_slug}",

    response_model=ThreadResponse,

)

def get_thread_by_slug(

    category_slug: str,

    thread_slug: str,

    db: Session = Depends(get_db),

):

    """

    Get a thread using:

        category slug

        thread slug

    """

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

    thread = db.scalar(

        select(Thread).where(

            Thread.slug == thread_slug,

            Thread.category_id == category.id,

        )

    )

    if not thread:

        raise HTTPException(

            status_code=404,

            detail="Thread not found",

        )

    thread.views += 1

    db.commit()

    db.refresh(thread)

    return thread

@router.get(

    "/{thread_id}",

    response_model=ThreadResponse,

)

def get_thread(

    thread_id: int,

    db: Session = Depends(get_db),

):

    """

    Get a thread by numeric ID.

    """

    thread = db.get(

        Thread,

        thread_id,

    )

    if not thread:

        raise HTTPException(

            status_code=404,

            detail="Thread not found",

        )

    thread.views += 1

    db.commit()

    db.refresh(thread)

    return thread

@router.post(

    "",

    response_model=ThreadResponse,

)

def create_thread(

    payload: ThreadCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    """

    Create a new forum discussion.

    """

    category = db.get(

        Category,

        payload.category_id,

    )

    if not category:

        raise HTTPException(

            status_code=404,

            detail="Category not found",

        )

    title = payload.title.strip()

    content = payload.content.strip()

    if len(title) < 3:

        raise HTTPException(

            status_code=422,

            detail="Thread title must be at least 3 characters",

        )

    if not content:

        raise HTTPException(

            status_code=422,
detail="Thread content cannot be empty",

        )

    slug = generate_unique_slug(

        db,

        title,

    )

    thread = Thread(

        title=title,

        slug=slug,

        content=content,

        category_id=category.id,

        author_id=current_user.id,
        problem=payload.problem,
        network_environment=payload.network_environment,
        symptoms=payload.symptoms,
        logs_alarms=payload.logs_alarms,
        what_i_tried=payload.what_i_tried,
    )

    db.add(thread)

    db.commit()

    db.refresh(thread)

    return thread