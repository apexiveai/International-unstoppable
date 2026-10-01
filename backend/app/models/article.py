from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Article(Base):

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(

        primary_key=True,

    )

    title: Mapped[str] = mapped_column(

        String(300),

        nullable=False,

        index=True,

    )

    slug: Mapped[str] = mapped_column(

        String(340),

        unique=True,

        nullable=False,

        index=True,

    )

    excerpt: Mapped[str] = mapped_column(

        String(600),

        nullable=False,

        default="",

    )

    content: Mapped[str] = mapped_column(

        Text,

        nullable=False,

    )

    category: Mapped[str] = mapped_column(

        String(100),

        nullable=False,

        index=True,

    )

    author_id: Mapped[int] = mapped_column(

        ForeignKey("users.id"),

        nullable=False,

        index=True,

    )

    cover_image_url: Mapped[str | None] = mapped_column(

        String(1000),

        nullable=True,

    )

    read_time_minutes: Mapped[int] = mapped_column(

        default=5,

        nullable=False,

    )

    views: Mapped[int] = mapped_column(

        default=0,

        nullable=False,

    )

    is_published: Mapped[bool] = mapped_column(

        default=True,

        nullable=False,

        index=True,

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

    author = relationship(

        "User",

    )