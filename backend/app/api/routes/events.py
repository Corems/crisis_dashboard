from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import EconomicEvent, get_session
from app.schemas.events import EconomicEventOut

router = APIRouter()


@router.get("/events", response_model=list[EconomicEventOut])
async def get_events(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(EconomicEvent).order_by(EconomicEvent.event_date))
    rows = result.scalars().all()
    return [
        EconomicEventOut(
            event_id=r.event_id,
            name=r.name,
            country=r.country,
            event_date=r.event_date.isoformat(),
            impact=r.impact,
            actual=r.actual,
            estimate=r.estimate,
            previous=r.previous,
            unit=r.unit,
        )
        for r in rows
    ]
