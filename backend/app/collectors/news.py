from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser

# RSS sources — add/remove as needed
RSS_FEEDS = [
    {"source": "Reuters", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"source": "FT", "url": "https://www.ft.com/rss/home"},
    {"source": "Zerohedge", "url": "https://feeds.feedburner.com/zerohedge/feed"},
    {"source": "ISW", "url": "https://www.understandingwar.org/rss.xml"},
    {"source": "Bloomberg", "url": "https://feeds.bloomberg.com/markets/news.rss"},
]

# keywords for filtering — keep only relevant items
KEYWORDS = [
    "recession",
    "fed",
    "inflation",
    "gdp",
    "unemployment",
    "crisis",
    "rate",
    "debt",
    "market",
    "economy",
    "war",
    "ukraine",
    "russia",
    "geopolit",
    "china",
    "dollar",
    "treasury",
]


def is_relevant(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in KEYWORDS)


def parse_date(entry) -> datetime | None:
    try:
        if hasattr(entry, "published"):
            return parsedate_to_datetime(entry.published).replace(tzinfo=None)
    except Exception:
        pass
    return None


async def collect_news() -> list[dict]:

    items = []

    for feed_cfg in RSS_FEEDS:
        try:
            # feedparser is synchronous but lightweight — fine for a daily cron
            feed = feedparser.parse(feed_cfg["url"])
            for entry in feed.entries[:30]:  # top 30 from each feed
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                url = entry.get("link", "")

                if not url or not title:
                    continue
                if not is_relevant(title, summary):
                    continue

                items.append(
                    {
                        "title": title[:512],
                        "summary": summary[:2000] if summary else None,
                        "url": url[:1024],
                        "source": feed_cfg["source"],
                        "published_at": parse_date(entry),
                        "fetched_at": datetime.utcnow(),
                    }
                )
        except Exception as e:
            print(f"RSS error [{feed_cfg['source']}]: {e}")

    return items
