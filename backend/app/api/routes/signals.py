import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import MarketSignals, get_session
from app.schemas.signals import MarketSignalsOut

router = APIRouter()


def _clean(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


@router.get("/signals/latest", response_model=MarketSignalsOut)
async def get_signals_latest(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MarketSignals).order_by(desc(MarketSignals.fetched_at)).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="No market signals data yet")
    return MarketSignalsOut(
        vix=_clean(row.vix),
        vix_ok=row.vix_ok,
        fear_greed_score=_clean(row.fear_greed_score),
        fear_greed_ok=row.fear_greed_ok,
        sp500_current=_clean(row.sp500_current),
        sp500_ma200=_clean(row.sp500_ma200),
        sp500_above_ma200=row.sp500_above_ma200,
        cape=_clean(row.cape),
        cape_ok=row.cape_ok,
        cot_crude_net=row.cot_crude_net,
        cot_crude_ok=row.cot_crude_ok,
        green_count=row.green_count,
        overall_signal=row.overall_signal,
        sp500_ath=_clean(row.sp500_ath),
        sp500_drawdown_pct=_clean(row.sp500_drawdown_pct),
        msci_ath=_clean(row.msci_ath),
        msci_current=_clean(row.msci_current),
        msci_drawdown_pct=_clean(row.msci_drawdown_pct),
        fetched_at=row.fetched_at.isoformat(),
    )
