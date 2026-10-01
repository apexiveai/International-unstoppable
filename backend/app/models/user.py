from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(

        primary_key=True,

    )

    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(

        String(50),

        unique=True,

        nullable=False,

        index=True,

    )

    email: Mapped[str] = mapped_column(

        String(255),

        unique=True,

        nullable=False,

        index=True,

    )

    password_hash: Mapped[str] = mapped_column(

        String(255),

        nullable=False,

    )

    display_name: Mapped[str] = mapped_column(

        String(100),

        nullable=False,

    )

    bio: Mapped[str] = mapped_column(

        String(500),

        default="",

        nullable=False,

    )

    is_active: Mapped[bool] = mapped_column(

        Boolean,

        default=True,

        nullable=False,

    )

    is_admin: Mapped[bool] = mapped_column(

        Boolean,

        default=False,

        nullable=False,

    )

    email_verified_at: Mapped[datetime | None] = mapped_column(

        DateTime,

        nullable=True,

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )

    threads = relationship(

        "Thread",

        back_populates="author",

    )

    replies = relationship(

        "Reply",

        back_populates="author",

    )