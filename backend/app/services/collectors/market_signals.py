async def collect_and_save() -> dict:
    from app.collectors.market_signals import collect_market_signals
    from app.models.db import MarketSignals, SessionLocal, init_db

    await init_db()
    async with SessionLocal() as session:
        row = await collect_market_signals(session)
        session.add(MarketSignals(**row))
        await session.commit()

    return {
        "overall_signal": row["overall_signal"],
        "green_count": row["green_count"],
        "collected_at": row["fetched_at"].isoformat(),
    }
