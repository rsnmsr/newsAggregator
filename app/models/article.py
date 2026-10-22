from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    feed_id: Mapped[int] = mapped_column(
        ForeignKey("feeds.id"),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    link: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    feed: Mapped["Feed"] = relationship(
        back_populates="articles",
    )

    __table_args__ = (
        UniqueConstraint(
            "feed_id",
            "external_id",
            name="uq_feed_article",
        ),
    )