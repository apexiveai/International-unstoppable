from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from app.auth import get_current_user

from app.database import get_db

from app.models import Reply, Thread, User
from app.services.notifications.service import (
    create_notification,
)
from app.schemas.reply import ReplyCreate, ReplyResponse

router = APIRouter(

    prefix="/api/replies",

    tags=["Replies"],

)

@router.get(

    "/thread/{thread_id}",

    response_model=list[ReplyResponse],

)

def get_replies(

    thread_id: int,

    db: Session = Depends(get_db),

):

    thread = db.get(Thread, thread_id)

    if not thread:

        raise HTTPException(

            status_code=404,

            detail="Thread not found",

        )

    return thread.replies

@router.post(

    "",

    response_model=ReplyResponse,

)

def create_reply(

    payload: ReplyCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    thread = db.get(

        Thread,

        payload.thread_id,

    )

    if not thread:

        raise HTTPException(

            status_code=404,

            detail="Thread not found",

        )

    reply = Reply(

        content=payload.content,

        thread_id=payload.thread_id,

        author_id=current_user.id,

    )

    if thread.author_id != current_user.id:

        create_notification(

            db,

            recipient_id=thread.author_id,

            actor_id=current_user.id,

            type="reply",

            title="New reply",

            message="Someone replied to your discussion.",

            link=(

                f"/forums/{thread.category.slug}"

                "/{thread.slug}"

            ),

            entity_type="thread",

            entity_id=thread.id,

        )
        db.add(reply)

        db.commit()

        db.refresh(reply)

    return reply