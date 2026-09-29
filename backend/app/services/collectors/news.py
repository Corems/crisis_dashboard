from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.news import collect_news
    from app.models.db import NewsItem, SessionLocal, init_db

    await init_db()
    news_data = await collect_news()

    async with SessionLocal() as session:
        for row in news_data:
            stmt = pg_insert(NewsItem).values(**row).on_conflict_do_nothing(index_elements=["url"])
            await session.execute(stmt)
        await session.commit()

    return {"news_collected": len(news_data), "collected_at": datetime.now(UTC).isoformat()}
