import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.core.config import settings

from app.database import get_db

from app.models import User

pwd_context = CryptContext(

    schemes=["bcrypt"],

    deprecated="auto",

)

oauth2_scheme = OAuth2PasswordBearer(

    tokenUrl="/api/auth/login",

)

def hash_password(password: str) -> str:

    return pwd_context.hash(password)


def generate_temporary_password() -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(18))


def verify_password(

    password: str,

    password_hash: str,

) -> bool:

    return pwd_context.verify(

        password,

        password_hash,

    )

def generate_secure_token() -> tuple[str, str]:

    raw_token = secrets.token_urlsafe(48)

    token_hash = hashlib.sha256(

        raw_token.encode("utf-8")

    ).hexdigest()

    return raw_token, token_hash

def hash_token(token: str) -> str:

    return hashlib.sha256(

        token.encode("utf-8")

    ).hexdigest()

def create_access_token(user_id: int) -> str:

    expire = datetime.now(timezone.utc) + timedelta(

        minutes=settings.access_token_expire_minutes

    )

    payload = {

        "sub": str(user_id),

        "exp": expire,

    }

    return jwt.encode(

        payload,

        settings.jwt_secret,

        algorithm=settings.jwt_algorithm,

    )

def get_current_user(

    token: str = Depends(oauth2_scheme),

    db: Session = Depends(get_db),

) -> User:

    credentials_exception = HTTPException(

        status_code=status.HTTP_401_UNAUTHORIZED,

        detail="Invalid authentication credentials",

        headers={

            "WWW-Authenticate": "Bearer",

        },

    )

    try:

        payload = jwt.decode(

            token,

            settings.jwt_secret,

            algorithms=[settings.jwt_algorithm],

        )

        user_id = payload.get("sub")

        if not user_id:

            raise credentials_exception

    except JWTError:

        raise credentials_exception

    user = db.get(User, int(user_id))

    if not user or not user.is_active:

        raise credentials_exception

    return user
