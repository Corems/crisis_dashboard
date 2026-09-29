from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Indicator


async def build_system_prompt(session: AsyncSession) -> str:
    # Latest record per fred_id (MAX(date) subquery)
    subq = (
        select(
            Indicator.fred_id,
            func.max(Indicator.date).label("max_date"),
        )
        .group_by(Indicator.fred_id)
        .subquery()
    )
    result = await session.execute(
        select(Indicator).join(
            subq,
            (Indicator.fred_id == subq.c.fred_id) & (Indicator.date == subq.c.max_date),
        )
    )
    rows = result.scalars().all()

    lines = [
        "You are a macroeconomic analyst assistant. Respond in Ukrainian.",
        "Here are the current macroeconomic indicators from the dashboard:",
        "",
    ]
    for r in rows:
        prev = f" (previous: {r.previous_value})" if r.previous_value is not None else ""
        lines.append(f"- {r.name}: {r.value}{prev}, score: {r.score}, date: {r.date}")
    lines.append("")
    lines.append("Use this data to answer user questions about macroeconomics, markets, and risks.")
    return "\n".join(lines)
