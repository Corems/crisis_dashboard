from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import BuffettFiling, BuffettHolding, get_session
from app.schemas.buffett import BuffettFilingOut, BuffettHoldingOut, BuffettHoldingsOut

router = APIRouter()


@router.get("/buffett/holdings", response_model=BuffettHoldingsOut)
async def get_buffett_holdings(session: AsyncSession = Depends(get_session)):
    filing_result = await session.execute(
        select(BuffettFiling).order_by(desc(BuffettFiling.filing_date)).limit(1)
    )
    filing = filing_result.scalar_one_or_none()
    if not filing:
        raise HTTPException(status_code=404, detail="No Berkshire 13F data yet")

    holdings_result = await session.execute(
        select(BuffettHolding)
        .where(BuffettHolding.accession_number == filing.accession_number)
        .order_by(desc(BuffettHolding.portfolio_pct))
    )
    holdings = holdings_result.scalars().all()
    return BuffettHoldingsOut(
        filing_date=filing.filing_date,
        period_of_report=filing.period_of_report,
        total_value_usd=filing.total_value_usd,
        holdings=[
            BuffettHoldingOut(
                ticker=h.ticker,
                company_name=h.company_name,
                value_usd=h.value_usd,
                shares=h.shares,
                portfolio_pct=h.portfolio_pct,
                change_type=h.change_type,
                change_pct=h.change_pct,
            )
            for h in holdings
        ],
    )


@router.get("/buffett/filings", response_model=list[BuffettFilingOut])
async def get_buffett_filings(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(BuffettFiling).order_by(desc(BuffettFiling.filing_date)).limit(10)
    )
    filings = result.scalars().all()
    return [
        BuffettFilingOut(
            accession_number=f.accession_number,
            filing_date=f.filing_date,
            period_of_report=f.period_of_report,
            total_value_usd=f.total_value_usd,
            fetched_at=f.fetched_at.isoformat(),
        )
        for f in filings
    ]
