import contextlib
import os
from datetime import datetime, timedelta

import httpx

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_BASE = "https://finnhub.io/api/v1"


async def collect_economic_calendar() -> list[dict]:

    today = datetime.utcnow().date()
    date_from = (today - timedelta(days=7)).isoformat()
    date_to = (today + timedelta(days=14)).isoformat()

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{FINNHUB_BASE}/calendar/economic",
                params={
                    "from": date_from,
                    "to": date_to,
                    "token": FINNHUB_API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Finnhub calendar error: {e}")
            return []

    events = []
    for item in data.get("economicCalendar", []):
        # US only, high/medium impact
        if item.get("country") != "US":
            continue
        impact = item.get("impact", "low")
        if impact not in ("high", "medium"):
            continue

        event_date_str = item.get("time") or item.get("date")
        if not event_date_str:
            continue

        try:
            event_date = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
        except Exception:
            continue

        events.append(
            {
                "event_id": str(item.get("id", f"{item.get('event', '')}_{event_date_str}")),
                "name": item.get("event", ""),
                "country": item.get("country", "US"),
                "event_date": event_date,
                "impact": impact,
                "actual": item.get("actual"),
                "estimate": item.get("estimate"),
                "previous": item.get("prev"),
                "unit": item.get("unit"),
                "fetched_at": datetime.utcnow(),
            }
        )

    print(f"Finnhub: collected {len(events)} US high/medium impact events")
    return events


async def collect_finnhub_news() -> list[dict]:

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{FINNHUB_BASE}/news",
                params={
                    "category": "general",
                    "token": FINNHUB_API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json()
        except Exception as e:
            print(f"Finnhub news error: {e}")
            return []

    news = []
    for item in items[:30]:  # top 30 items
        url = item.get("url", "")
        if not url:
            continue

        published_at = None
        ts = item.get("datetime")
        if ts:
            with contextlib.suppress(ValueError, OverflowError, OSError, TypeError):
                published_at = datetime.utcfromtimestamp(ts)

        news.append(
            {
                "title": item.get("headline", "")[:512],
                "summary": item.get("summary", "")[:2048] if item.get("summary") else None,
                "url": url[:1024],
                "source": f"finnhub:{item.get('source', 'unknown')}",
                "published_at": published_at,
                "fetched_at": datetime.utcnow(),
            }
        )

    print(f"Finnhub: collected {len(news)} news items")
    return news
