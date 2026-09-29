from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import FedBalance, get_session
from app.schemas.fed_balance import FedBalanceOut

router = APIRouter()


@router.get("/fed/balance", response_model=list[FedBalanceOut])
async def get_fed_balance(session: AsyncSession = Depends(get_session)):
    subq = (
        select(func.max(FedBalance.period).label("max_period"), FedBalance.series_id)
        .group_by(FedBalance.series_id)
        .subquery()
    )
    result = await session.execute(
        select(FedBalance).join(
            subq,
            (FedBalance.series_id == subq.c.series_id) & (FedBalance.period == subq.c.max_period),
        )
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No Fed balance sheet data yet")
    return [
        FedBalanceOut(
            period=r.period.isoformat(),
            series_id=r.series_id,
            name=r.name,
            value_bln=r.value_bln,
            wow_change=r.wow_change,
            wow_change_pct=r.wow_change_pct,
            yoy_change=r.yoy_change,
            yoy_change_pct=r.yoy_change_pct,
        )
        for r in rows
    ]
