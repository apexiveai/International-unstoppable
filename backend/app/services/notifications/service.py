from sqlalchemy.orm import Session

from app.models.notification import Notification

def create_notification(

    db: Session,

    *,

    recipient_id: int,

    type: str,

    title: str,

    message: str,

    actor_id: int | None = None,

    link: str | None = None,

    entity_type: str | None = None,

    entity_id: int | None = None,

) -> Notification:

    notification = Notification(

        recipient_id=recipient_id,

        actor_id=actor_id,

        type=type,

        title=title,

        message=message,

        link=link,

        entity_type=entity_type,

        entity_id=entity_id,

    )

    db.add(notification)

    return notification