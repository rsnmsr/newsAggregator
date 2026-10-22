# This services fetch RSS feed and can call rss parser
import feedparser

rss_feeds = {'bbc':'https://feeds.bbci.co.uk/news/rss.xml',
             'techcrunch':'https://techcrunch.com/feed/',
             'theverge': 'https://www.theverge.com/rss/index.xml',
             'wired':'https://www.wired.com/feed/rss',
             'ycombinator': 'https://news.ycombinator.com/rss',
             'huggingface':'https://huggingface.co/blog/feed.xml',
             'github':'https://github.blog/feed/',
             'bleeping': 'https://www.bleepingcomputer.com/feed/',
             'nature':'https://www.nature.com/nature.rss',
             'nasa': 'https://www.nasa.gov/news-release/feed/',
             'business_standard': 'https://www.business-standard.com/rss/home_page_top_stories.rss',
             'npr': 'https://feeds.npr.org/1001/rss.xml',
             'livemint':'https://www.livemint.com/rss/news',
             'producthunt':'https://www.producthunt.com/feed'}

async def get_feed():
    return list(rss_feeds.keys())

