from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        unique=True,
        nullable=False,
    )

    etag: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    last_modified: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    articles: Mapped[list["Article"]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )