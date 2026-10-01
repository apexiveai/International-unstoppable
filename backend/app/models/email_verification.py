from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class EmailVerificationToken(Base):

    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(

        primary_key=True

    )

    user_id: Mapped[int] = mapped_column(

        ForeignKey("users.id"),

        nullable=False,

        index=True,

    )

    token_hash: Mapped[str] = mapped_column(

        String(255),

        nullable=False,

        unique=True,

    )

    expires_at: Mapped[datetime] = mapped_column(

        DateTime,

        nullable=False,

    )

    used_at: Mapped[datetime | None] = mapped_column(

        DateTime,

        nullable=True,

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )