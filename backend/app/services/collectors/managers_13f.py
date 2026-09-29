from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.managers_13f import collect_all
    from app.models.db import ManagerFiling, ManagerHolding, SessionLocal, init_db

    await init_db()
    all_managers = await collect_all()

    async with SessionLocal() as session:
        for data in all_managers:
            filing = data["filing"]

            stmt = (
                pg_insert(ManagerFiling)
                .values(**filing)
                .on_conflict_do_update(
                    constraint="uq_manager_filing",
                    set_={
                        "total_value_usd": filing["total_value_usd"],
                        "fetched_at": filing["fetched_at"],
                    },
                )
            )
            await session.execute(stmt)

            for row in data["holdings"]:
                holding_row = {k: v for k, v in row.items()}
                holding_row["accession_number"] = filing["accession_number"]
                stmt = (
                    pg_insert(ManagerHolding)
                    .values(**holding_row)
                    .on_conflict_do_update(
                        constraint="uq_manager_holding",
                        set_={
                            "value_usd": holding_row["value_usd"],
                            "shares": holding_row["shares"],
                            "portfolio_pct": holding_row["portfolio_pct"],
                            "change_type": holding_row["change_type"],
                            "change_pct": holding_row["change_pct"],
                        },
                    )
                )
                await session.execute(stmt)

        await session.commit()

    total_holdings = sum(len(d["holdings"]) for d in all_managers)
    return {
        "managers_collected": len(all_managers),
        "holdings_stored": total_holdings,
        "collected_at": datetime.now(UTC).isoformat(),
    }
