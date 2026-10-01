from fastapi import APIRouter, Depends

from sqlalchemy import func, select

from sqlalchemy.orm import Session

from app.api.auth import get_current_user

from app.database import get_db

from app.models.notification import Notification

from app.schemas.notification import (

    NotificationResponse,

    NotificationUnreadCount,

)

router = APIRouter(

    prefix="/api/notifications",

    tags=["Notifications"],

)

@router.get(

    "",

    response_model=list[NotificationResponse],

)

def get_notifications(

    page: int = 1,

    limit: int = 30,

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user),

):

    offset = (page - 1) * limit

    result = db.execute(

        select(Notification)

        .where(

            Notification.recipient_id

            == current_user.id

        )

        .order_by(

            Notification.created_at.desc()

        )

        .offset(offset)

        .limit(limit)

    )

    return result.scalars().all()

@router.get(

    "/unread-count",

    response_model=NotificationUnreadCount,

)

def unread_count(

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user),

):

    count = db.execute(

        select(

            func.count(Notification.id)

        )

        .where(

            Notification.recipient_id

            == current_user.id,

            Notification.is_read.is_(False),

        )

    ).scalar_one()

    return {

        "count": count

    }

@router.patch(

    "/{notification_id}/read",

)

def mark_read(

    notification_id: int,

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user),

):

    notification = db.execute(

        select(Notification)

        .where(

            Notification.id == notification_id,

            Notification.recipient_id

            == current_user.id,

        )

    ).scalar_one_or_none()

    if notification:

        notification.is_read = True

        db.commit()

    return {

        "success": True

    }

@router.patch(

    "/read-all",

)

def mark_all_read(

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user),

):

    db.query(Notification).filter(

        Notification.recipient_id

        == current_user.id,

        Notification.is_read.is_(False),

    ).update(

        {

            Notification.is_read: True

        },

        synchronize_session=False,

    )

    db.commit()

    return {

        "success": True

    }