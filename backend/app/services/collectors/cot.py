from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.cot import collect_all
    from app.models.db import CotReport, SessionLocal, init_db

    await init_db()
    rows = await collect_all()

    async with SessionLocal() as session:
        for row in rows:
            stmt = (
                pg_insert(CotReport)
                .values(**row)
                .on_conflict_do_update(
                    constraint="uq_cot_report_date_instrument",
                    set_={
                        "noncomm_long": row["noncomm_long"],
                        "noncomm_short": row["noncomm_short"],
                        "noncomm_net": row["noncomm_net"],
                        "noncomm_net_pct_oi": row["noncomm_net_pct_oi"],
                        "comm_long": row["comm_long"],
                        "comm_short": row["comm_short"],
                        "open_interest": row["open_interest"],
                        "net_change_wow": row["net_change_wow"],
                    },
                )
            )
            await session.execute(stmt)
        await session.commit()

    return {"rows_stored": len(rows), "collected_at": datetime.now(UTC).isoformat()}
