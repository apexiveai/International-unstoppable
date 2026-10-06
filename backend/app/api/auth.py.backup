from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import or_, select

from sqlalchemy.orm import Session

from app.auth import (

    create_access_token,

    get_current_user,

    hash_password,

    verify_password,

)

from app.database import get_db

from app.models import Tenant, User

from app.schemas.auth import (

    LoginRequest,

    RegisterRequest,

    TokenResponse,

    UserResponse,

)
from app.schemas.didit import (
    FaceCompleteRequest,
    FaceCompleteResponse,
    FaceRegisterCompleteRequest,
    FaceSessionRequest,
    FaceSessionResponse,
)
from app.services.didit import create_session, get_session_status

router = APIRouter(

    prefix="/api/auth",

    tags=["Authentication"],

)

@router.post(

    "/face/session",

    response_model=FaceSessionResponse,

)

def face_session(payload: FaceSessionRequest):

    return create_session(

        payload.email,

        payload.return_to,

    )

def _get_approved_face_result(session_id: str) -> dict:

    result = get_session_status(session_id)

    print("===== DIDIT FACE DECISION =====")

    print(result)

    print("================================")

    status_value = str(

        result.get("status") or ""

    ).strip()

    # Didit's current decision statuses.

    if status_value != "Approved":

        if status_value == "In Review":

            raise HTTPException(

                status_code=status.HTTP_202_ACCEPTED,

                detail="Face verification is under review.",

            )

        if status_value in {

            "Declined",

            "Expired",

            "Not Finished",

        }:

            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,

                detail=f"Face verification status: {status_value}",

            )

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail=f"Face verification has not been approved. "

                   f"Current status: {status_value or 'Unknown'}",

        )

    return result

@router.post(

    "/face/complete",

    response_model=FaceCompleteResponse,

)

def complete_face_session(

    payload: FaceCompleteRequest,

    db: Session = Depends(get_db),

):

    result = _get_approved_face_result(payload.session_id)

    vendor_data = result.get("vendor_data")

    if not isinstance(vendor_data, str) or not vendor_data.strip():

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Didit session is not linked to an account.",

        )

    user = db.scalar(

        select(User).where(

            User.email == vendor_data.strip()

        )

    )

    if not user or not user.is_active:

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="No active account is linked to this verification.",

        )

    token = create_access_token(user.id)

    return {

        "access_token": token,

        "token_type": "bearer",

        "user": user,

    }

@router.post(

    "/face/register/complete",

    response_model=TokenResponse,

    status_code=status.HTTP_201_CREATED,

)

def complete_face_registration(

    payload: FaceRegisterCompleteRequest,

    db: Session = Depends(get_db),

):

    result = _get_approved_face_result(payload.session_id)

    vendor_data = result.get("vendor_data")

    if (

        not isinstance(vendor_data, str)

        or vendor_data.strip().casefold() != payload.email.casefold()

    ):

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Face verification is not linked to this email address.",

        )

    return register(payload, db)

@router.post(

    "/register",

    response_model=TokenResponse,

    status_code=status.HTTP_201_CREATED,

)

def register(

    payload: RegisterRequest,

    db: Session = Depends(get_db),

):

    existing = db.scalar(

        select(User).where(

            or_(

                User.email == payload.email,

                User.username == payload.username,

            )

        )

    )

    if existing:

        raise HTTPException(

            status_code=409,

            detail="Email or username already exists",

        )

    user = User(

        username=payload.username,

        email=payload.email,

        password_hash=hash_password(

            payload.password

        ),

        display_name=payload.display_name,
    )
    tenant = Tenant(
        name=f"{payload.display_name} Workspace",
        slug=f"{payload.username}-workspace",
    )
    db.add(tenant)
    db.flush()
    user.tenant_id = tenant.id

    db.add(user)

    db.commit()

    db.refresh(user)

    token = create_access_token(user.id)

    return {

        "access_token": token,

        "token_type": "bearer",

        "user": user,

    }

@router.post(

    "/login",

    response_model=TokenResponse,

)

def login(

    payload: LoginRequest,

    db: Session = Depends(get_db),

):

    user = db.scalar(

        select(User).where(

            User.email == payload.email

        )

    )

    if not user or not verify_password(

        payload.password,

        user.password_hash,

    ):

        raise HTTPException(

            status_code=401,

            detail="Invalid email or password",

        )

    token = create_access_token(user.id)

    return {

        "access_token": token,

        "token_type": "bearer",

        "user": user,

    }

@router.get(

    "/me",

    response_model=UserResponse,

)

def me(

    current_user: User = Depends(

        get_current_user

    ),

):

    return current_user