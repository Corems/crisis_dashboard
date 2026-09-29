from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.fed_balance import collect_all
    from app.models.db import FedBalance, SessionLocal, init_db

    await init_db()
    rows = await collect_all()

    async with SessionLocal() as session:
        for row in rows:
            stmt = (
                pg_insert(FedBalance)
                .values(**row)
                .on_conflict_do_update(
                    constraint="uq_fed_balance_period_series",
                    set_={
                        "value_bln": row["value_bln"],
                        "wow_change": row["wow_change"],
                        "wow_change_pct": row["wow_change_pct"],
                        "yoy_change": row["yoy_change"],
                        "yoy_change_pct": row["yoy_change_pct"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

    return {"rows_stored": len(rows), "collected_at": datetime.now(UTC).isoformat()}
