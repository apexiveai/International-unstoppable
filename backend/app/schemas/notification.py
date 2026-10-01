from datetime import datetime

from pydantic import BaseModel, ConfigDict

class NotificationResponse(BaseModel):

    id: int

    actor_id: int | None

    type: str

    title: str

    message: str

    link: str | None

    entity_type: str | None

    entity_id: int | None

    is_read: bool

    created_at: datetime

    model_config = ConfigDict(

        from_attributes=True,

    )

class NotificationUnreadCount(BaseModel):

    count: int