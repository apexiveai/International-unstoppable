from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Category(Base):

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(

        String(120),

        unique=True,

        nullable=False,

        index=True,

    )

    slug: Mapped[str] = mapped_column(

        String(140),

        unique=True,

        nullable=False,

        index=True,

    )

    description: Mapped[str] = mapped_column(

        Text,

        nullable=False,
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(

        DateTime,

        default=datetime.utcnow,

        nullable=False,

    )

    threads = relationship(

        "Thread",

        back_populates="category",

        cascade="all, delete-orphan",

    )