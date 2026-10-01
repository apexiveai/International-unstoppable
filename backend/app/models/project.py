from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Project(Base):

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(

        primary_key=True,

    )

    name: Mapped[str] = mapped_column(

        String(200),

        nullable=False,

        index=True,

    )

    slug: Mapped[str] = mapped_column(

        String(240),

        unique=True,

        nullable=False,

        index=True,

    )

    description: Mapped[str] = mapped_column(

        String(800),

        nullable=False,

        default="",

    )

    content: Mapped[str] = mapped_column(

        Text,

        nullable=False,

        default="",

    )

    category: Mapped[str] = mapped_column(

        String(100),

        nullable=False,

        index=True,

    )

    creator_id: Mapped[int] = mapped_column(

        ForeignKey("users.id"),

        nullable=False,

        index=True,

    )

    repository_url: Mapped[str | None] = mapped_column(

        String(1000),

        nullable=True,

    )

    website_url: Mapped[str | None] = mapped_column(

        String(1000),

        nullable=True,

    )

    logo_url: Mapped[str | None] = mapped_column(

        String(1000),

        nullable=True,

    )

    status: Mapped[str] = mapped_column(

        String(50),

        nullable=False,

        default="Building",

        index=True,

    )

    stars: Mapped[int] = mapped_column(

        default=0,

        nullable=False,

    )

    views: Mapped[int] = mapped_column(

        default=0,

        nullable=False,

    )

    is_featured: Mapped[bool] = mapped_column(

        default=False,

        nullable=False,

        index=True,

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )

    updated_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        onupdate=datetime.utcnow,

        nullable=False,

    )

    creator = relationship(

        "User",

    )