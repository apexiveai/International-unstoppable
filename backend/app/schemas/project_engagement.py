from pydantic import BaseModel, Field


class TechnologyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class EngagementResponse(BaseModel):
    project_id: int
    likes: int
    bookmarks: int
    followers: int
    liked: bool
    bookmarked: bool
    followed: bool
