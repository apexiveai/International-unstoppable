from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):

    username: str = Field(

        min_length=3,

        max_length=50,

    )

    email: EmailStr

    password: str = Field(

        min_length=8,

        max_length=128,

    )

    display_name: str = Field(

        min_length=2,

        max_length=100,

    )

class LoginRequest(BaseModel):

    email: EmailStr

    password: str

class UserResponse(BaseModel):

    id: int

    username: str

    email: EmailStr

    display_name: str

    bio: str

    is_active: bool

    is_admin: bool

    tenant_id: int | None = None

    class Config:

        from_attributes = True

class TokenResponse(BaseModel):

    access_token: str

    token_type: str

    user: UserResponse