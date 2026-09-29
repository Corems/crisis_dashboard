from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import IndexComparison, get_session
from app.schemas.index_comparison import ChartPoint, IndexPeriodData

router = APIRouter()


@router.get("/indices/comparison", response_model=list[IndexPeriodData])
async def get_index_comparison(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(IndexComparison).order_by(IndexComparison.ticker, IndexComparison.period)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No index comparison data yet")
    return [
        IndexPeriodData(
            ticker=r.ticker,
            period=r.period,
            return_pct=r.return_pct,
            current_price=r.current_price,
            chart_data=[ChartPoint(**p) for p in (r.chart_data or [])],
            fetched_at=r.fetched_at.isoformat(),
        )
        for r in rows
    ]
