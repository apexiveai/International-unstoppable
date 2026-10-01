from datetime import datetime

from pydantic import BaseModel, ConfigDict

class CategoryCreate(BaseModel):

    name: str

    slug: str

    description: str

class CategoryResponse(CategoryCreate):

    id: int

    parent_id: int | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)