from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.cpi import collect_all
    from app.models.db import CpiComponent, SessionLocal, init_db

    await init_db()
    rows = await collect_all()

    async with SessionLocal() as session:
        for row in rows:
            stmt = (
                pg_insert(CpiComponent)
                .values(**row)
                .on_conflict_do_update(
                    constraint="uq_cpi_period_series",
                    set_={
                        "value": row["value"],
                        "yoy_change_pct": row["yoy_change_pct"],
                        "mom_change_pct": row["mom_change_pct"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

    return {"rows_stored": len(rows), "collected_at": datetime.now(UTC).isoformat()}
