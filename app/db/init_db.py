from app.db.base import Base
from app.db.sessions import SessionLocal, engine
from app.models import Feed, Article


DEFAULT_FEEDS = (
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://news.ycombinator.com/rss",
    "https://huggingface.co/blog/feed.xml",
    "https://github.blog/feed/",
    "https://www.bleepingcomputer.com/feed/",
    "https://www.nature.com/nature.rss",
    "https://www.nasa.gov/news-release/feed/",
    "https://www.business-standard.com/rss/home_page_top_stories.rss",
    "https://feeds.npr.org/1001/rss.xml",
    "https://livemint.com/rss/news",
)


def init_db():
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")
        connection.exec_driver_sql("PRAGMA busy_timeout=30000")

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        for url in DEFAULT_FEEDS:
            if not db.query(Feed).filter(Feed.url == url).first():
                db.add(Feed(url=url))
        db.commit()


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")