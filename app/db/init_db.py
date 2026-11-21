from app.db.base import Base
from app.db.sessions import SessionLocal, engine
from app.models import RSSSource


DEFAULT_SOURCES = (
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

        tables = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        if "feeds" in tables and "rss_sources" not in tables:
            connection.exec_driver_sql("ALTER TABLE feeds RENAME TO rss_sources")

        if "articles" in {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }:
            article_columns = {
                row[1]
                for row in connection.exec_driver_sql("PRAGMA table_info(articles)")
            }
            if "feed_id" in article_columns and "source_id" not in article_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE articles RENAME COLUMN feed_id TO source_id"
                )

            article_columns = {
                row[1]
                for row in connection.exec_driver_sql("PRAGMA table_info(articles)")
            }
            if "published_day" not in article_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE articles ADD COLUMN published_day VARCHAR(10)"
                )
            connection.exec_driver_sql(
                "UPDATE articles "
                "SET published_day = substr(published_at, 1, 10) "
                "WHERE published_day IS NULL AND published_at IS NOT NULL"
            )
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_articles_source_published_day "
                "ON articles (source_id, published_day)"
            )

        connection.commit()

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        for url in DEFAULT_SOURCES:
            if not db.query(RSSSource).filter(RSSSource.url == url).first():
                db.add(RSSSource(url=url))
        db.commit()


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")