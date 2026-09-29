from datetime import date


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.yahoo import collect_yahoo
    from app.models.db import Indicator, SessionLocal, init_db

    await init_db()
    yahoo_data = await collect_yahoo()
    today = date.today()

    async with SessionLocal() as session:
        for row in yahoo_data:
            stmt = (
                pg_insert(Indicator)
                .values(
                    **row,
                    score=0.0,
                    date=today,
                )
                .on_conflict_do_update(
                    constraint="uq_indicator_fred_date",
                    set_={
                        "value": row["value"],
                        "previous_value": row["previous_value"],
                        "fetched_at": row["fetched_at"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

    return {"yahoo_collected": len(yahoo_data), "collected_at": today.isoformat()}
