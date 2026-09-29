from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import CotReport, get_session
from app.schemas.cot import CotReportOut

router = APIRouter()


@router.get("/cot/latest", response_model=list[CotReportOut])
async def get_cot_latest(session: AsyncSession = Depends(get_session)):
    subq = (
        select(func.max(CotReport.report_date).label("max_date"), CotReport.instrument)
        .group_by(CotReport.instrument)
        .subquery()
    )
    result = await session.execute(
        select(CotReport).join(
            subq,
            (CotReport.instrument == subq.c.instrument)
            & (CotReport.report_date == subq.c.max_date),
        )
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No COT data yet")
    return [
        CotReportOut(
            report_date=r.report_date.isoformat(),
            instrument=r.instrument,
            noncomm_long=r.noncomm_long,
            noncomm_short=r.noncomm_short,
            noncomm_net=r.noncomm_net,
            noncomm_net_pct_oi=r.noncomm_net_pct_oi,
            comm_long=r.comm_long,
            comm_short=r.comm_short,
            open_interest=r.open_interest,
            net_change_wow=r.net_change_wow,
        )
        for r in rows
    ]


@router.get("/cot/history", response_model=list[CotReportOut])
async def get_cot_history(
    instrument: str,
    weeks: int = 52,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(CotReport)
        .where(CotReport.instrument == instrument)
        .order_by(desc(CotReport.report_date))
        .limit(weeks)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No COT data for instrument '{instrument}'")
    return [
        CotReportOut(
            report_date=r.report_date.isoformat(),
            instrument=r.instrument,
            noncomm_long=r.noncomm_long,
            noncomm_short=r.noncomm_short,
            noncomm_net=r.noncomm_net,
            noncomm_net_pct_oi=r.noncomm_net_pct_oi,
            comm_long=r.comm_long,
            comm_short=r.comm_short,
            open_interest=r.open_interest,
            net_change_wow=r.net_change_wow,
        )
        for r in rows
    ]
