from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.authorization import require_admin
from app.database import get_db
from app.models import ChatConversation, ChatMessage, SystemAuditEvent, User
from app.schemas.chatbot import ChatMessageRequest
from app.services.chatbot import generate_answer

router = APIRouter(prefix="/api/chatbot", tags=["AI Chatbot"])


class ChatMessageResponse(BaseModel):
    conversation_id: int
    answer: str
    allowed: bool
    category: str


class ChatMessageItem(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatConversationItem(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    username: str
    email: str
    title: str
    created_at: datetime
    updated_at: datetime


def _record_admin_chat_access(
    db: Session,
    admin: User,
    conversation: ChatConversation,
    action: str,
) -> None:
    db.add(
        SystemAuditEvent(
            tenant_id=conversation.tenant_id,
            actor_user_id=admin.id,
            action=action,
            target_type="chat_conversation",
            target_id=str(conversation.id),
            outcome="success",
            details='{"access":"admin_monitoring"}',
        )
    )


@router.post("/message", response_model=ChatMessageResponse)
def chatbot_message(
    payload: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.is_active or user.account_status != "ACTIVE":
        raise HTTPException(status_code=403, detail="An active account is required.")
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant.")

    if payload.conversation_id is None:
        chat = ChatConversation(
            tenant_id=user.tenant_id,
            user_id=user.id,
            title=payload.message.strip()[:157] + ("..." if len(payload.message.strip()) > 157 else ""),
        )
        db.add(chat)
        db.flush()
    else:
        chat = db.scalar(
            select(ChatConversation).where(
                ChatConversation.id == payload.conversation_id,
                ChatConversation.tenant_id == user.tenant_id,
                ChatConversation.user_id == user.id,
            )
        )
        if chat is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

    answer, allowed, category = generate_answer(payload.message)
    db.add_all(
        [
            ChatMessage(
                conversation_id=chat.id,
                tenant_id=user.tenant_id,
                role="user",
                content=payload.message,
            ),
            ChatMessage(
                conversation_id=chat.id,
                tenant_id=user.tenant_id,
                role="assistant",
                content=answer,
            ),
        ]
    )
    chat.updated_at = datetime.utcnow()
    db.commit()
    return ChatMessageResponse(
        conversation_id=chat.id,
        answer=answer,
        allowed=allowed,
        category=category,
    )


@router.get("/conversations")
def list_my_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant.")
    rows = db.execute(
        select(ChatConversation, func.count(ChatMessage.id).label("message_count"))
        .outerjoin(ChatMessage, ChatMessage.conversation_id == ChatConversation.id)
        .where(
            ChatConversation.tenant_id == user.tenant_id,
            ChatConversation.user_id == user.id,
        )
        .group_by(ChatConversation.id)
        .order_by(desc(ChatConversation.updated_at))
    ).all()
    return {
        "items": [
            {
                "id": chat.id,
                "title": chat.title,
                "message_count": count,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at,
            }
            for chat, count in rows
        ]
    }


@router.get("/conversations/{conversation_id}", response_model=list[ChatMessageItem])
def get_my_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.scalar(
        select(ChatConversation).where(
            ChatConversation.id == conversation_id,
            ChatConversation.tenant_id == user.tenant_id,
            ChatConversation.user_id == user.id,
        )
    )
    if chat is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return db.scalars(
        select(ChatMessage)
        .where(
            ChatMessage.conversation_id == chat.id,
            ChatMessage.tenant_id == user.tenant_id,
        )
        .order_by(ChatMessage.created_at, ChatMessage.id)
    ).all()


@router.get("/admin/conversations")
def admin_list_conversations(
    q: str = Query(default="", max_length=200),
    tenant_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1, le=100),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = (
        select(ChatConversation, User)
        .join(User, User.id == ChatConversation.user_id)
    )
    if tenant_id is not None:
        query = query.where(ChatConversation.tenant_id == tenant_id)
    if q.strip():
        search = f"%{q.strip()}%"
        query = query.where(
            or_(
                ChatConversation.title.ilike(search),
                User.username.ilike(search),
                User.email.ilike(search),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(desc(ChatConversation.updated_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    for chat, _user in rows:
        _record_admin_chat_access(db, admin, chat, "admin.chat_conversation_listed")
    if rows:
        db.commit()
    return {
        "items": [
            ChatConversationItem(
                id=chat.id,
                tenant_id=chat.tenant_id,
                user_id=owner.id,
                username=owner.username,
                email=owner.email,
                title=chat.title,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
            )
            for chat, owner in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": min(100, (total + page_size - 1) // page_size),
    }


@router.get("/admin/conversations/{conversation_id}")
def admin_get_conversation(
    conversation_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    chat = db.get(ChatConversation, conversation_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    _record_admin_chat_access(db, admin, chat, "admin.chat_conversation_read")
    messages = db.scalars(
        select(ChatMessage)
        .where(
            ChatMessage.conversation_id == chat.id,
            ChatMessage.tenant_id == chat.tenant_id,
        )
        .order_by(ChatMessage.created_at, ChatMessage.id)
    ).all()
    db.commit()
    return {
        "conversation": {
            "id": chat.id,
            "tenant_id": chat.tenant_id,
            "user_id": chat.user_id,
            "title": chat.title,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
        },
        "messages": messages,
    }