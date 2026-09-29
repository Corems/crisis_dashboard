from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.index_comparison import collect_index_comparison
    from app.models.db import IndexComparison, SessionLocal, init_db

    await init_db()
    rows = await collect_index_comparison()

    async with SessionLocal() as session:
        for row in rows:
            stmt = (
                pg_insert(IndexComparison)
                .values(**row)
                .on_conflict_do_update(
                    constraint="uq_index_comparison_ticker_period",
                    set_={
                        "return_pct": row["return_pct"],
                        "current_price": row["current_price"],
                        "chart_data": row["chart_data"],
                        "fetched_at": row["fetched_at"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

    return {"rows_stored": len(rows), "collected_at": datetime.now(UTC).isoformat()}
