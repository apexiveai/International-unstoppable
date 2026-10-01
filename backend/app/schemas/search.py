from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectSearchResult(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    category: str
    status: str
    technologies: list[str]
    semantic_score: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
