from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import CpiComponent, get_session
from app.schemas.cpi import CpiComponentOut

router = APIRouter()


@router.get("/cpi/latest", response_model=list[CpiComponentOut])
async def get_cpi_latest(session: AsyncSession = Depends(get_session)):
    subq = (
        select(func.max(CpiComponent.period).label("max_period"), CpiComponent.series_id)
        .group_by(CpiComponent.series_id)
        .subquery()
    )
    result = await session.execute(
        select(CpiComponent).join(
            subq,
            (CpiComponent.series_id == subq.c.series_id)
            & (CpiComponent.period == subq.c.max_period),
        )
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No CPI data yet")
    return [
        CpiComponentOut(
            period=r.period.isoformat(),
            series_id=r.series_id,
            name=r.name,
            value=r.value,
            yoy_change_pct=r.yoy_change_pct,
            mom_change_pct=r.mom_change_pct,
        )
        for r in rows
    ]
