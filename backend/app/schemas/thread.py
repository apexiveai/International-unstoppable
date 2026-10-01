from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class ThreadCreate(BaseModel):

    title: str = Field(..., min_length=3, max_length=300)

    content: str = Field(..., min_length=1)

    category_id: int
    problem: str | None = None
    network_environment: str | None = None
    symptoms: str | None = None
    logs_alarms: str | None = None
    what_i_tried: str | None = None

class ThreadResponse(BaseModel):

    id: int

    title: str

    slug: str

    content: str

    category_id: int

    author_id: int

    views: int

    created_at: datetime

    updated_at: datetime
    problem: str | None = None
    network_environment: str | None = None
    symptoms: str | None = None
    logs_alarms: str | None = None
    what_i_tried: str | None = None

    model_config = ConfigDict(from_attributes=True)