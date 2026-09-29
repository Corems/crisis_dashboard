from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import EiaPetroleum, get_session
from app.schemas.eia import EiaPetroleumOut

router = APIRouter()


@router.get("/eia/petroleum", response_model=list[EiaPetroleumOut])
async def get_eia_petroleum(session: AsyncSession = Depends(get_session)):
    subq = (
        select(func.max(EiaPetroleum.period).label("max_period"), EiaPetroleum.product)
        .group_by(EiaPetroleum.product)
        .subquery()
    )
    result = await session.execute(
        select(EiaPetroleum).join(
            subq,
            (EiaPetroleum.product == subq.c.product) & (EiaPetroleum.period == subq.c.max_period),
        )
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No EIA petroleum data yet")
    return [
        EiaPetroleumOut(
            period=r.period.isoformat(),
            product=r.product,
            value_mbbl=r.value_mbbl,
            wow_change=r.wow_change,
            wow_change_pct=r.wow_change_pct,
            five_year_avg=r.five_year_avg,
        )
        for r in rows
    ]
