from fastapi import APIRouter

from app.schemas.chatbot import (

    ChatMessageRequest,

    ChatMessageResponse,

)

from app.services.chatbot import generate_answer

router = APIRouter(

    prefix="/api/chatbot",

    tags=["AI Chatbot"],

)

@router.post(

    "/message",

    response_model=ChatMessageResponse,

)

def chatbot_message(

    payload: ChatMessageRequest,

):

    answer, allowed, category = generate_answer(

        payload.message

    )

    return ChatMessageResponse(

        answer=answer,

        allowed=allowed,

        category=category,

    )