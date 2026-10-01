from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ResourceBase(BaseModel):

    title: str

    slug: str

    description: str = ""

    content: str = ""

    resource_type: str

    category: str

    file_url: str | None = None

    file_size: str | None = None

    is_featured: bool = False

    is_published: bool = True

class ResourceCreate(ResourceBase):

    pass

class ResourceResponse(ResourceBase):

    id: int

    author_id: int

    downloads: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(

        from_attributes=True,

    )