import feedparser
import logging
import hashlib
import calendar
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.sessions import SessionLocal
from app.models import Article, RSSSource


logger = logging.getLogger(__name__)


def _entry_id(entry):
    external_id = getattr(entry, "id", None) or getattr(entry, "guid", None)
    if not external_id:
        external_id = getattr(entry, "link", None)
    if not external_id:
        fingerprint = (
            f"{getattr(entry, 'title', '')}"
            f"{getattr(entry, 'published', getattr(entry, 'updated', ''))}"
            f"{getattr(entry, 'summary', '')}"
        )
        external_id = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return str(external_id)[:2048]


def _entry_datetime(entry, field):
    parsed = getattr(entry, f"{field}_parsed", None)
    if parsed is not None:
        return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
    return None


def _entry_published_day(entry):
    published_at = _entry_datetime(entry, "published")
    if published_at is None:
        published_at = _entry_datetime(entry, "updated")
    if published_at is None:
        published_at = datetime.now(timezone.utc)
    return published_at.date().isoformat()


def fetch_articles(db: Session):
    new_article_table = []

    sources = db.query(RSSSource).order_by(RSSSource.id).all()
    logger.info("Fetching %d saved RSS sources", len(sources))

    for source in sources:
        logger.info("Fetching RSS source id=%d url=%s", source.id, source.url)
        parsed_feed = feedparser.parse(
            source.url,
            etag=source.etag,
            modified=source.last_modified,
        )

        if parsed_feed.bozo:
            logger.warning(
                "Could not fully parse RSS source id=%d url=%s: %s",
                source.id,
                source.url,
                parsed_feed.bozo_exception,
            )

        logger.info(
            "Parsed RSS source id=%d url=%s: %d entries",
            source.id,
            source.url,
            len(parsed_feed.entries),
        )

        source.etag = parsed_feed.get("etag")
        source.last_modified = parsed_feed.get("modified")
        source.last_fetched_at = datetime.now(timezone.utc)

        entries_by_external_id = {
            _entry_id(entry): entry
            for entry in parsed_feed.entries
        }

        existing_ids = set()
        ids_by_day = {}
        for external_id, entry in entries_by_external_id.items():
            published_day = _entry_published_day(entry)
            ids_by_day.setdefault(published_day, []).append(external_id)

        for published_day, external_ids in ids_by_day.items():
            for start in range(0, len(external_ids), 500):
                chunk = external_ids[start:start + 500]
                existing_ids.update(
                    db.execute(
                        select(Article.external_id).where(
                            Article.source_id == source.id,
                            Article.published_day == published_day,
                            Article.external_id.in_(chunk),
                        )
                    ).scalars()
                )

        for entry in parsed_feed.entries:
            external_id = _entry_id(entry)
            if external_id in existing_ids:
                continue

            title = getattr(getattr(entry, "title_detail", None), "value", None)
            if title is None:
                title = getattr(entry, "title", "")

            published_at = _entry_datetime(entry, "published")
            updated_at = _entry_datetime(entry, "updated")
            published_day = _entry_published_day(entry)

            db.add(
                Article(
                    source_id=source.id,
                    external_id=external_id,
                    title=title,
                    link=getattr(entry, "link", None),
                    published_at=published_at,
                    updated_at=updated_at,
                    published_day=published_day,
                )
            )

            new_article_table.append(
                {
                    "title": title,
                    "url": getattr(entry, "link", ""),
                    "published": getattr(
                        entry,
                        "published",
                        getattr(entry, "updated", ""),
                    ),
                    "summary": getattr(entry, "summary", ""),
                    "source": source.url,
                }
            )
            existing_ids.add(external_id)

    db.commit()
    logger.info("Stored %d new articles", len(new_article_table))
    return new_article_table


def get_articles(db: Session):
    return fetch_articles(db)


if __name__ == "__main__":
    with SessionLocal() as db:
        fetch_articles(db)