from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import AiAnalysis, get_session
from app.schemas.analysis import AiAnalysisOut

router = APIRouter()


@router.get("/analysis/latest", response_model=AiAnalysisOut)
async def get_latest_analysis(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(AiAnalysis).order_by(desc(AiAnalysis.generated_at)).limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="No AI analysis yet")
    return AiAnalysisOut(
        id=row.id,
        situation=row.situation,
        whales=row.whales,
        signals=row.signals or [],
        risk_level=row.risk_level,
        risk_explanation=row.risk_explanation,
        investor_action=row.investor_action,
        generated_at=row.generated_at.isoformat(),
        cached=row.is_cached,
    )


@router.post("/analysis/generate", response_model=AiAnalysisOut)
async def generate_analysis_endpoint(
    force: bool = False,
    model: str | None = None,
):
    from app.collectors.ai_analyst import generate_analysis

    try:
        result = await generate_analysis(
            force=force,
            provider_override=None,
            model_override=model,
        )
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    return AiAnalysisOut(**result)
