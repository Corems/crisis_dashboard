from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import NewsItem, get_session
from app.schemas.news import NewsItemOut

router = APIRouter()


@router.get("/news", response_model=list[NewsItemOut])
async def get_news(
    limit: int = 20,
    source: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(NewsItem).order_by(desc(NewsItem.published_at)).limit(limit)
    )
    rows = result.scalars().all()
    out = []
    for r in rows:
        if source and r.source != source:
            continue
        out.append(
            NewsItemOut(
                id=r.id,
                title=r.title,
                summary=r.summary,
                source=r.source,
                url=r.url,
                published_at=r.published_at.isoformat() if r.published_at else None,
            )
        )
    return out
