import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.stock_fundamental import analyze_stock
from app.models.db import StockAnalysis, get_session
from app.schemas.stock import StockFundamentalsOut, YouTubeAnalyzeRequest, YouTubeAnalyzeResponse
from app.services.ai_client import AIClient

router = APIRouter(tags=["youtube"])

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "youtube_analyze.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Config not found: {CONFIG_PATH}",
        )
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@router.post("/youtube/analyze", response_model=YouTubeAnalyzeResponse)
async def analyze_youtube(request: YouTubeAnalyzeRequest):
    transcript = request.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript is empty")

    config = _load_config()
    system_prompt = config["system_prompt"]

    try:
        analysis = await AIClient().complete(
            prompt=f"Video transcript:\n\n{transcript}",
            system=system_prompt,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e

    return YouTubeAnalyzeResponse(transcript=transcript, analysis=analysis)


@router.get("/stock/analyze", response_model=StockFundamentalsOut, tags=["stock"])
async def get_stock_analysis(
    ticker: str,
    force: bool = False,
    session: AsyncSession = Depends(get_session),
):
    ticker = ticker.upper().strip()
    schema_fields = set(StockFundamentalsOut.model_fields.keys())
    datetime_fields = {"fetched_at", "generated_at", "expires_at"}

    def to_out(obj, cached: bool) -> StockFundamentalsOut:
        return StockFundamentalsOut(
            **{
                f: getattr(obj, f).isoformat() if f in datetime_fields else getattr(obj, f)
                for f in schema_fields
                if f != "cached" and hasattr(obj, f)
            },
            cached=cached,
        )

    # Check cache unless force
    if not force:
        result = await session.execute(
            select(StockAnalysis)
            .where(StockAnalysis.ticker == ticker)
            .order_by(StockAnalysis.fetched_at.desc())
            .limit(1)
        )
        cached_row = result.scalar_one_or_none()
        if cached_row and cached_row.expires_at.replace(tzinfo=UTC) > datetime.now(UTC):
            return to_out(cached_row, cached=True)

    # Fresh fetch
    try:
        data = await analyze_stock(ticker)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch {ticker}: {e}") from e

    # Upsert
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    values = {k: v for k, v in data.items() if k != "ticker"}
    stmt = (
        pg_insert(StockAnalysis)
        .values(ticker=ticker, **values)
        .on_conflict_do_update(
            constraint="uq_stock_analysis_ticker",
            set_=values,
        )
    )
    await session.execute(stmt)
    await session.commit()

    # Re-read from DB
    result = await session.execute(select(StockAnalysis).where(StockAnalysis.ticker == ticker))
    row = result.scalar_one()

    return to_out(row, cached=False)
