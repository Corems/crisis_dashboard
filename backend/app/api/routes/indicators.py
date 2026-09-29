from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Indicator, get_session
from app.schemas.indicators import HintOut, IndicatorOut, IndicatorsOut
from app.services.indicators import calculate_score

router = APIRouter()


@router.get("/indicators", response_model=IndicatorsOut)
async def get_indicators(session: AsyncSession = Depends(get_session)):
    subq = select(func.max(Indicator.id).label("max_id")).group_by(Indicator.fred_id).subquery()
    result = await session.execute(select(Indicator).where(Indicator.id.in_(select(subq))))
    rows = result.scalars().all()
    date_lookup = {r.fred_id: r for r in rows}
    raw = [
        {
            "fred_id": r.fred_id,
            "name": r.name,
            "value": r.value,
            "previous_value": r.previous_value,
            "weight": r.weight,
            "score": r.score,
        }
        for r in rows
    ]
    scored, total = calculate_score(raw)
    return IndicatorsOut(
        indicators=[
            IndicatorOut(
                fred_id=s.fred_id,
                name=s.name,
                category=s.category,
                value=s.value,
                delta=s.delta,
                weight=s.weight,
                score=s.score,
                hint=HintOut(**s.hint) if s.hint else None,
                date=date_lookup[s.fred_id].date.isoformat() if s.fred_id in date_lookup else None,
                update_frequency=s.update_frequency,
                fetched_at=date_lookup[s.fred_id].fetched_at.isoformat()
                if s.fred_id in date_lookup and date_lookup[s.fred_id].fetched_at
                else None,
                inverted=s.inverted,
            )
            for s in scored
        ],
        total_score=total,
        calculated_at=datetime.utcnow().isoformat(),
    )
