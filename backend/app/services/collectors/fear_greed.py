from datetime import UTC, datetime, timedelta


async def collect_and_save() -> dict:
    from sqlalchemy import delete

    from app.collectors.fear_greed import collect_fear_greed
    from app.models.db import FearGreed, SessionLocal, init_db

    await init_db()
    row = await collect_fear_greed()

    async with SessionLocal() as session:
        session.add(FearGreed(**row))
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=90)
        await session.execute(delete(FearGreed).where(FearGreed.fetched_at < cutoff))
        await session.commit()

    return {
        "score": row["score"],
        "rating": row["rating"],
        "collected_at": row["fetched_at"].isoformat(),
    }
