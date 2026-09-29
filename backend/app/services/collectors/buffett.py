from datetime import UTC, datetime


async def collect_and_save() -> dict:
    from sqlalchemy import desc, select
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.collectors.buffett import collect_buffett
    from app.models.db import BuffettFiling, BuffettHolding, SessionLocal, init_db

    await init_db()

    # Check if we already have the latest filing
    async with SessionLocal() as session:
        result = await session.execute(
            select(BuffettFiling).order_by(desc(BuffettFiling.filing_date)).limit(1)
        )
        latest_in_db = result.scalar_one_or_none()

    data = await collect_buffett()
    filing = data["filing"]

    # Skip if this accession is already stored
    if latest_in_db and latest_in_db.accession_number == filing["accession_number"]:
        return {"filing": filing["accession_number"], "status": "already_in_db"}

    async with SessionLocal() as session:
        stmt = (
            pg_insert(BuffettFiling)
            .values(**filing)
            .on_conflict_do_update(
                constraint="uq_buffett_filing_accession",
                set_={
                    "total_value_usd": filing["total_value_usd"],
                    "fetched_at": filing["fetched_at"],
                },
            )
        )
        await session.execute(stmt)

        for row in data["holdings"]:
            holding_row = {k: v for k, v in row.items() if k != "filing_date"}
            holding_row["accession_number"] = filing["accession_number"]
            holding_row["filing_date"] = filing["filing_date"]
            stmt = (
                pg_insert(BuffettHolding)
                .values(**holding_row)
                .on_conflict_do_update(
                    constraint="uq_buffett_holding",
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

    return {
        "filing": filing["accession_number"],
        "holdings_stored": len(data["holdings"]),
        "collected_at": datetime.now(UTC).isoformat(),
    }
