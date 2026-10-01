from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Thread(Base):

    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(

        primary_key=True

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

    content: Mapped[str] = mapped_column(

        Text,

        nullable=False,
    )

    problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    network_environment: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs_alarms: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_i_tried: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[int] = mapped_column(

        ForeignKey("categories.id"),

        nullable=False,

        index=True,

    )

    author_id: Mapped[int] = mapped_column(

        ForeignKey("users.id"),

        nullable=False,

        index=True,

    )

    views: Mapped[int] = mapped_column(

        default=0,

        nullable=False,

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

    category = relationship(

        "Category",

        back_populates="threads",

    )

    author = relationship(

        "User",

        back_populates="threads",

    )

    replies = relationship(

        "Reply",

        back_populates="thread",

        cascade="all, delete-orphan",

    )