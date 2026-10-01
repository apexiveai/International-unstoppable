from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Reply(Base):

    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(

        primary_key=True

    )

    content: Mapped[str] = mapped_column(

        Text,

        nullable=False,

    )

    thread_id: Mapped[int] = mapped_column(

        ForeignKey("threads.id"),

        nullable=False,

        index=True,

    )

    author_id: Mapped[int] = mapped_column(

        ForeignKey("users.id"),

        nullable=False,

        index=True,

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )

    thread = relationship(

        "Thread",

        back_populates="replies",

    )

    author = relationship(

        "User",

        back_populates="replies",

    )