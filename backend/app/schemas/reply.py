from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ReplyCreate(BaseModel):

    content: str

    thread_id: int

class ReplyResponse(ReplyCreate):

    id: int

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)