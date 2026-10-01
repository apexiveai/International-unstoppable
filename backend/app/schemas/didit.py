from pydantic import BaseModel, EmailStr

from app.schemas.auth import RegisterRequest, UserResponse


class FaceSessionRequest(BaseModel):
    email: EmailStr
    return_to: str


class FaceSessionResponse(BaseModel):
    session_id: str
    verification_url: str


class FaceCompleteRequest(BaseModel):
    session_id: str


class FaceRegisterCompleteRequest(RegisterRequest):
    session_id: str


class FaceCompleteResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
