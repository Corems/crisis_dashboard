from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.finnhub import collect_economic_calendar, collect_finnhub_news
    from app.models.db import EconomicEvent, NewsItem, SessionLocal, init_db

    await init_db()

    events = await collect_economic_calendar()
    async with SessionLocal() as session:
        for row in events:
            stmt = (
                pg_insert(EconomicEvent)
                .values(**row)
                .on_conflict_do_update(
                    constraint="uq_economic_event_id",
                    set_={
                        "actual": row["actual"],
                        "estimate": row["estimate"],
                        "previous": row["previous"],
                        "fetched_at": row["fetched_at"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

    news = await collect_finnhub_news()
    async with SessionLocal() as session:
        for row in news:
            stmt = pg_insert(NewsItem).values(**row).on_conflict_do_nothing(index_elements=["url"])
            await session.execute(stmt)
        await session.commit()

    return {
        "events_collected": len(events),
        "news_collected": len(news),
        "collected_at": datetime.now(UTC).isoformat(),
    }
