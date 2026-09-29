from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import ManagerFiling, ManagerHolding, get_session
from app.schemas.managers import ManagerHoldingOut, ManagerHoldingsOut

router = APIRouter()


def _manager_holdings_out(
    filing: ManagerFiling, holdings: list[ManagerHolding]
) -> ManagerHoldingsOut:
    return ManagerHoldingsOut(
        manager_key=filing.manager_key,
        manager_name=filing.manager_name,
        filing_date=filing.filing_date,
        period_of_report=filing.period_of_report,
        total_value_usd=filing.total_value_usd,
        holdings=[
            ManagerHoldingOut(
                ticker=h.ticker,
                company_name=h.company_name,
                value_usd=h.value_usd,
                shares=h.shares,
                portfolio_pct=h.portfolio_pct,
                change_type=h.change_type,
                change_pct=h.change_pct,
            )
            for h in sorted(holdings, key=lambda x: x.portfolio_pct, reverse=True)
        ],
    )


async def _get_latest_manager_filing(session, manager_key: str) -> ManagerFiling | None:
    result = await session.execute(
        select(ManagerFiling)
        .where(ManagerFiling.manager_key == manager_key)
        .order_by(desc(ManagerFiling.filing_date))
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/managers/holdings", response_model=list[ManagerHoldingsOut])
async def get_managers_holdings(session: AsyncSession = Depends(get_session)):
    from app.collectors.managers_13f import MANAGERS

    result = []
    for manager_key in MANAGERS:
        filing = await _get_latest_manager_filing(session, manager_key)
        if not filing:
            continue
        hr = await session.execute(
            select(ManagerHolding)
            .where(ManagerHolding.manager_key == manager_key)
            .where(ManagerHolding.accession_number == filing.accession_number)
        )
        holdings = hr.scalars().all()
        result.append(_manager_holdings_out(filing, holdings))
    if not result:
        raise HTTPException(status_code=404, detail="No manager 13F data yet")
    return result


@router.get("/managers/holdings/{manager_key}", response_model=ManagerHoldingsOut)
async def get_manager_holdings(manager_key: str, session: AsyncSession = Depends(get_session)):
    filing = await _get_latest_manager_filing(session, manager_key)
    if not filing:
        raise HTTPException(status_code=404, detail=f"No 13F data for '{manager_key}'")
    hr = await session.execute(
        select(ManagerHolding)
        .where(ManagerHolding.manager_key == manager_key)
        .where(ManagerHolding.accession_number == filing.accession_number)
    )
    holdings = hr.scalars().all()
    return _manager_holdings_out(filing, holdings)
