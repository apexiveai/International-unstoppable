from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):

    name: str

    slug: str

    description: str = ""

    content: str = ""

    category: str

    repository_url: str | None = None

    website_url: str | None = None

    logo_url: str | None = None

    status: str = "Building"

    is_featured: bool = False

class ProjectCreate(ProjectBase):

    pass

class ProjectResponse(ProjectBase):

    id: int

    creator_id: int

    stars: int

    views: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(

        from_attributes=True,

    )