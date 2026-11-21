import feedparser
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.sessions import SessionLocal
from app.models import Feed


logger = logging.getLogger(__name__)


def fetch_rss(db: Session):
    article_table = []

    saved_feeds = db.query(Feed).order_by(Feed.id).all()
    logger.info("Fetching %d saved RSS feeds", len(saved_feeds))

    for saved_feed in saved_feeds:
        logger.info("Fetching RSS feed id=%d url=%s", saved_feed.id, saved_feed.url)
        parsed_feed = feedparser.parse(saved_feed.url)

        if parsed_feed.bozo:
            logger.warning(
                "Could not fully parse RSS feed id=%d url=%s: %s",
                saved_feed.id,
                saved_feed.url,
                parsed_feed.bozo_exception,
            )

        logger.info(
            "Parsed RSS feed id=%d url=%s: %d entries",
            saved_feed.id,
            saved_feed.url,
            len(parsed_feed.entries),
        )

        saved_feed.etag = parsed_feed.get("etag")
        saved_feed.last_modified = parsed_feed.get("modified")
        saved_feed.last_fetched_at = datetime.now(timezone.utc)

        for entry in parsed_feed.entries:
            title = getattr(getattr(entry, "title_detail", None), "value", None)
            if title is None:
                title = getattr(entry, "title", "")

            article = {
                "title": title,
                "url": getattr(entry, "link", ""),
                "published": getattr(entry, "published", getattr(entry, "updated", "")),
                "summary": getattr(entry, "summary", ""),
                "source": saved_feed.url,
            }
            article_table.append(article)

    db.commit()
    return article_table


def get_feed(db: Session):
    return fetch_rss(db)


if __name__ == "__main__":
    with SessionLocal() as db:
        fetch_rss(db)