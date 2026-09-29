from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import FearGreed, get_session
from app.schemas.fear_greed import FearGreedOut

router = APIRouter()


@router.get("/fear-greed/latest", response_model=FearGreedOut)
async def get_fear_greed_latest(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(FearGreed).order_by(desc(FearGreed.fetched_at)).limit(1))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="No Fear & Greed data yet")
    return FearGreedOut(
        score=row.score,
        rating=row.rating,
        previous_close=row.previous_close,
        one_week_ago=row.one_week_ago,
        one_month_ago=row.one_month_ago,
        fetched_at=row.fetched_at.isoformat(),
    )
