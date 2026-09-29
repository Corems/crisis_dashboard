from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import MarketSignals, get_session, init_db

router = APIRouter(prefix="/collect")


@router.post("/indicators")
async def collect_indicators():
    from app.services.collectors.fred import collect_and_save

    return await collect_and_save()


@router.post("/news")
async def collect_news_endpoint():
    from app.services.collectors.news import collect_and_save

    return await collect_and_save()


@router.post("/yahoo")
async def collect_yahoo_endpoint():
    from app.services.collectors.yahoo import collect_and_save

    return await collect_and_save()


@router.post("/finnhub")
async def collect_finnhub_endpoint():
    from app.services.collectors.finnhub import collect_and_save

    return await collect_and_save()


@router.post("/buffett")
async def collect_buffett_endpoint():
    from app.services.collectors.buffett import collect_and_save

    return await collect_and_save()


@router.post("/managers_13f")
async def collect_managers_13f_endpoint():
    from app.services.collectors.managers_13f import collect_and_save

    return await collect_and_save()


@router.post("/eia")
async def collect_eia_endpoint():
    from app.services.collectors.eia import collect_and_save

    return await collect_and_save()


@router.post("/fed_balance")
async def collect_fed_balance_endpoint():
    from app.services.collectors.fed_balance import collect_and_save

    return await collect_and_save()


@router.post("/cpi")
async def collect_cpi_endpoint():
    from app.services.collectors.cpi import collect_and_save

    return await collect_and_save()


@router.post("/cot")
async def collect_cot_endpoint():
    from app.services.collectors.cot import collect_and_save

    return await collect_and_save()


@router.post("/fear_greed")
async def collect_fear_greed_endpoint():
    from app.services.collectors.fear_greed import collect_and_save

    return await collect_and_save()


@router.post("/signals")
async def collect_signals_endpoint(session: AsyncSession = Depends(get_session)):
    from app.collectors.market_signals import collect_market_signals

    await init_db()
    row = await collect_market_signals(session)
    session.add(MarketSignals(**row))
    await session.commit()
    return {
        "overall_signal": row["overall_signal"],
        "green_count": row["green_count"],
        "collected_at": row["fetched_at"].isoformat(),
    }


@router.post("/index_comparison")
async def collect_index_comparison_endpoint():
    from app.services.collectors.index_comparison import collect_and_save

    return await collect_and_save()


@router.post("/pmi")
async def collect_pmi_endpoint():
    from app.services.collectors.pmi import collect_and_save

    return await collect_and_save()
