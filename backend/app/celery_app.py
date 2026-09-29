import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("crisis", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.beat_schedule = {
    # FRED indicators once a day at 16:00 UTC
    "collect-indicators-daily": {
        "task": "app.celery_app.collect_indicators",
        "schedule": crontab(hour=16, minute=0),
    },
    # Yahoo + RSS news every 30 minutes
    "collect-yahoo-and-news": {
        "task": "app.celery_app.collect_yahoo_and_news",
        "schedule": crontab(minute="*/30"),
    },
    # Finnhub calendar + news once an hour
    "collect-finnhub-hourly": {
        "task": "app.celery_app.collect_finnhub",
        "schedule": crontab(minute=5),  # at minute 5 of every hour
    },
    # Berkshire 13F — once a week on Monday at 10:00 UTC (13F is quarterly; more frequent checks are unnecessary)
    "collect-buffett-weekly": {
        "task": "app.celery_app.collect_buffett",
        "schedule": crontab(hour=10, minute=0, day_of_week=1),
    },
    # Multi-manager 13F (Bridgewater, Scion, Pershing) — Monday at 11:00 UTC
    "collect-managers-13f-weekly": {
        "task": "app.celery_app.collect_managers_13f",
        "schedule": crontab(hour=11, minute=0, day_of_week=1),
    },
    # EIA Weekly Petroleum Report — every Wednesday at 16:00 UTC (EIA publishes ~10:30 ET = 15:30 UTC)
    "collect-eia-weekly": {
        "task": "app.celery_app.collect_eia",
        "schedule": crontab(hour=16, minute=0, day_of_week=3),
    },
    # Fed H.4.1 Balance Sheet — every Thursday at 21:30 UTC (Fed publishes ~16:30 ET)
    "collect-fed-balance-weekly": {
        "task": "app.celery_app.collect_fed_balance",
        "schedule": crontab(hour=21, minute=30, day_of_week=4),
    },
    # BLS CPI — 15th of each month at 14:00 UTC (BLS publishes ~2 weeks after month end)
    "collect-cpi-monthly": {
        "task": "app.celery_app.collect_cpi",
        "schedule": crontab(hour=14, minute=0, day_of_month=15),
    },
    # CFTC COT Report — every Friday at 21:00 UTC (CFTC publishes ~15:30 ET)
    "collect-cot-weekly": {
        "task": "app.celery_app.collect_cot",
        "schedule": crontab(hour=21, minute=0, day_of_week=5),
    },
    # AI macro analyst — daily at 17:00 UTC (after all data has been collected)
    "generate-ai-analysis-daily": {
        "task": "app.celery_app.generate_ai_analysis",
        "schedule": crontab(hour=17, minute=0),
    },
    # CNN Fear & Greed Index — every hour at :00
    "collect-fear-greed-hourly": {
        "task": "app.celery_app.collect_fear_greed",
        "schedule": crontab(minute=0),
    },
    # S&P 500 vs MSCI World — every 30 minutes
    "collect-index-comparison": {
        "task": "app.celery_app.collect_index_comparison",
        "schedule": crontab(minute="*/30"),
    },
    # Market signals (Entry signals + Drawdown) — every hour at :15
    "collect-market-signals-hourly": {
        "task": "app.celery_app.collect_market_signals",
        "schedule": crontab(minute=15),
    },
}

celery_app.conf.timezone = "UTC"


@celery_app.task
def collect_indicators():
    import asyncio

    asyncio.run(_collect_indicators())


@celery_app.task
def collect_yahoo_and_news():
    import asyncio

    asyncio.run(_collect_yahoo_and_news())


@celery_app.task
def collect_finnhub():
    import asyncio

    asyncio.run(_collect_finnhub())


@celery_app.task
def collect_buffett():
    import asyncio

    asyncio.run(_collect_buffett())


@celery_app.task
def collect_managers_13f():
    import asyncio

    asyncio.run(_collect_managers_13f())


@celery_app.task
def collect_eia():
    import asyncio

    asyncio.run(_collect_eia())


@celery_app.task
def collect_fed_balance():
    import asyncio

    asyncio.run(_collect_fed_balance())


@celery_app.task
def collect_cpi():
    import asyncio

    asyncio.run(_collect_cpi())


@celery_app.task
def collect_cot():
    import asyncio

    asyncio.run(_collect_cot())


@celery_app.task
def generate_ai_analysis():
    import asyncio

    asyncio.run(_generate_ai_analysis())


@celery_app.task
def collect_fear_greed():
    import asyncio

    asyncio.run(_collect_fear_greed())


@celery_app.task
def collect_index_comparison():
    import asyncio

    asyncio.run(_collect_index_comparison())


@celery_app.task
def collect_market_signals():
    import asyncio

    asyncio.run(_collect_market_signals())


async def _collect_indicators():
    from app.services.collectors.fred import collect_and_save

    result = await collect_and_save()
    print(f"Collected {result.get('indicators_collected', 0)} FRED indicators")


async def _collect_yahoo_and_news():
    from app.services.collectors.news import collect_and_save as collect_news
    from app.services.collectors.yahoo import collect_and_save as collect_yahoo

    result = await collect_yahoo()
    print(f"Collected {result.get('yahoo_collected', 0)} Yahoo indicators")

    result = await collect_news()
    print(f"Collected {result.get('news_collected', 0)} news items")


async def _collect_finnhub():
    from app.services.collectors.finnhub import collect_and_save

    result = await collect_and_save()
    print(
        f"Collected {result.get('events_collected', 0)} economic events, {result.get('news_collected', 0)} Finnhub news"
    )


async def _collect_buffett():
    from app.services.collectors.buffett import collect_and_save

    result = await collect_and_save()
    print(f"Buffett: {result}")


async def _collect_managers_13f():
    from app.services.collectors.managers_13f import collect_and_save

    result = await collect_and_save()
    print(f"managers_13f: stored {result.get('managers_collected', 0)} managers")


async def _collect_eia():
    from app.services.collectors.eia import collect_and_save

    result = await collect_and_save()
    print(f"EIA: stored {result.get('rows_stored', 0)} petroleum rows")


async def _collect_fed_balance():
    from app.services.collectors.fed_balance import collect_and_save

    result = await collect_and_save()
    print(f"FedBalance: stored {result.get('rows_stored', 0)} rows")


async def _collect_cpi():
    from app.services.collectors.cpi import collect_and_save

    result = await collect_and_save()
    print(f"CPI: stored {result.get('rows_stored', 0)} rows")


async def _generate_ai_analysis():
    from app.collectors.ai_analyst import generate_analysis

    result = await generate_analysis(force=True)
    print(f"AI analyst: generated analysis id={result['id']}, risk={result['risk_level']}")


async def _collect_index_comparison():
    from app.services.collectors.index_comparison import collect_and_save

    result = await collect_and_save()
    print(f"IndexComparison: stored {result.get('rows_stored', 0)} rows")


async def _collect_fear_greed():
    from app.services.collectors.fear_greed import collect_and_save

    result = await collect_and_save()
    print(f"Fear & Greed: stored score={result.get('score')} rating={result.get('rating')}")


async def _collect_cot():
    from app.services.collectors.cot import collect_and_save

    result = await collect_and_save()
    print(f"COT: stored {result.get('rows_stored', 0)} rows")


async def _collect_market_signals():
    from app.services.collectors.market_signals import collect_and_save

    result = await collect_and_save()
    print(
        f"MarketSignals: signal={result.get('overall_signal')} green={result.get('green_count')}/5"
    )
