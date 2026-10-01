from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import desc, select

from sqlalchemy.orm import Session

from app.auth import get_current_user

from app.database import get_db

from app.models import Article, User

from app.schemas.article import ArticleCreate, ArticleResponse

router = APIRouter(

    prefix="/api/articles",

    tags=["Articles"],

)

@router.get(

    "",

    response_model=list[ArticleResponse],

)

def list_articles(

    db: Session = Depends(get_db),

):

    articles = db.scalars(

        select(Article)

        .where(Article.is_published.is_(True))

        .order_by(desc(Article.created_at))

    ).all()

    return articles

@router.get(

    "/featured",

    response_model=list[ArticleResponse],

)

def featured_articles(

    db: Session = Depends(get_db),

):

    articles = db.scalars(

        select(Article)

        .where(

            Article.is_published.is_(True),

            Article.is_featured.is_(True),

        )

        .order_by(desc(Article.created_at))

    ).all()

    return articles

@router.get(

    "/{slug}",

    response_model=ArticleResponse,

)

def get_article(

    slug: str,

    db: Session = Depends(get_db),

):

    article = db.scalar(

        select(Article).where(

            Article.slug == slug,

            Article.is_published.is_(True),

        )

    )

    if not article:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,

            detail="Article not found",

        )

    article.views += 1

    db.commit()

    db.refresh(article)

    return article

@router.post(

    "",

    response_model=ArticleResponse,

    status_code=status.HTTP_201_CREATED,

)

def create_article(

    payload: ArticleCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    existing = db.scalar(

        select(Article).where(

            Article.slug == payload.slug,

        )

    )

    if existing:

        raise HTTPException(

            status_code=status.HTTP_409_CONFLICT,

            detail="Article slug already exists",

        )

    is_published = payload.is_published if current_user.is_admin else False
    is_featured = payload.is_featured if current_user.is_admin else False

    article = Article(
        title=payload.title,

        slug=payload.slug,

        excerpt=payload.excerpt,

        content=payload.content,

        category=payload.category,

        author_id=current_user.id,

        cover_image_url=payload.cover_image_url,

        read_time_minutes=payload.read_time_minutes,

        is_published=is_published,

        is_featured=is_featured

    )

    db.add(article)

    db.commit()

    db.refresh(article)

    return article