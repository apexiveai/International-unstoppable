from datetime import datetime

from sqlalchemy import (

    Boolean,

    DateTime,

    ForeignKey,

    Integer,

    String,

    Text,

)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Notification(Base):

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(

        Integer,

        primary_key=True,

    )

    recipient_id: Mapped[int] = mapped_column(

        ForeignKey("users.id"),

        nullable=False,

        index=True,

    )

    actor_id: Mapped[int | None] = mapped_column(

        ForeignKey("users.id"),

        nullable=True,

        index=True,

    )

    type: Mapped[str] = mapped_column(

        String(50),

        nullable=False,

        index=True,

    )

    title: Mapped[str] = mapped_column(

        String(200),

        nullable=False,

    )

    message: Mapped[str] = mapped_column(

        Text,

        nullable=False,

    )

    link: Mapped[str | None] = mapped_column(

        String(500),

        nullable=True,

    )

    entity_type: Mapped[str | None] = mapped_column(

        String(50),

        nullable=True,

    )

    entity_id: Mapped[int | None] = mapped_column(

        Integer,

        nullable=True,

    )

    is_read: Mapped[bool] = mapped_column(

        Boolean,

        default=False,

        nullable=False,

        index=True,

    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

        index=True,

    )

    recipient = relationship(

        "User",

        foreign_keys=[recipient_id],

    )

    actor = relationship(

        "User",

        foreign_keys=[actor_id],

    )