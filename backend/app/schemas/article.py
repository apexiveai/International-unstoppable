from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ArticleBase(BaseModel):

    title: str

    slug: str

    excerpt: str = ""

    content: str

    category: str

    cover_image_url: str | None = None

    read_time_minutes: int = 5

    is_published: bool = True

    is_featured: bool = False

class ArticleCreate(ArticleBase):

    pass

class ArticleResponse(ArticleBase):

    id: int

    author_id: int

    views: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(

        from_attributes=True,

    )