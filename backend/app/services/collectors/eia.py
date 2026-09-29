from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.eia import collect_all
    from app.models.db import EiaPetroleum, SessionLocal, init_db

    await init_db()
    rows = await collect_all()

    async with SessionLocal() as session:
        for row in rows:
            stmt = (
                pg_insert(EiaPetroleum)
                .values(**row)
                .on_conflict_do_update(
                    constraint="uq_eia_petroleum_period_product",
                    set_={
                        "value_mbbl": row["value_mbbl"],
                        "wow_change": row["wow_change"],
                        "wow_change_pct": row["wow_change_pct"],
                        "five_year_avg": row["five_year_avg"],
                        "fetched_at": row["fetched_at"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

    return {"rows_stored": len(rows), "collected_at": datetime.now(UTC).isoformat()}
