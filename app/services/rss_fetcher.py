# This services fetch RSS feed and can call rss parser
import feedparser
import json

rss_feeds = {'bbc':'https://feeds.bbci.co.uk/news/rss.xml',
             'techcrunch':'https://techcrunch.com/feed/',
             'theverge': 'https://www.theverge.com/rss/index.xml',
             'ycombinator': 'https://news.ycombinator.com/rss',
             'huggingface':'https://huggingface.co/blog/feed.xml',
             'github':'https://github.blog/feed/',
             'bleeping': 'https://www.bleepingcomputer.com/feed/',
             'nature':'https://www.nature.com/nature.rss',
             'nasa': 'https://www.nasa.gov/news-release/feed/',
             'business_standard': 'https://www.business-standard.com/rss/home_page_top_stories.rss',
             'npr': 'https://feeds.npr.org/1001/rss.xml',
             'livemint':'https://www.livemint.com/rss/news',
             }

async def get_feed():
    fetch_rss()
    return fetch_rss()

def fetch_rss():
    article_table = []
    for url_source,url_key in rss_feeds.items():
        feed = feedparser.parse(url_key)
        etag = feed.get("etag")
        modified = feed.get("modified")
        for entry in feed.entries:
            article = {
                "title": entry.title_detail.value,
                "url": entry.link,
                "published": entry.published if hasattr(entry, 'published') else entry.updated if hasattr(entry, 'updated') else '',
                "summary": entry.summary if hasattr(entry, 'summary') else '',
                "source": url_source,
            }
            article_table.append(article)
    return json.dumps(article_table)


if __name__=="__main__":
    fetch_rss()