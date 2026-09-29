from datetime import date, datetime

from sqlalchemy import desc, func, select

from app.models.db import Indicator, NewsItem, SessionLocal
from app.services.indicators import calculate_score

# import generated proto code
try:
    from app.grpc import crisis_pb2, crisis_pb2_grpc
except ImportError:
    crisis_pb2 = None
    crisis_pb2_grpc = None


class CrisisServicer:
    async def GetIndicators(self, request, context):
        async with SessionLocal() as session:
            last_date_result = await session.execute(select(func.max(Indicator.date)))
            last_date = last_date_result.scalar() or date.today()

            result = await session.execute(select(Indicator).where(Indicator.date == last_date))
            rows = result.scalars().all()

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

        scored, total_score = calculate_score(raw)

        indicators_proto = []
        for s in scored:
            indicators_proto.append(
                crisis_pb2.Indicator(
                    id=s.fred_id,
                    name=s.name,
                    value=s.value,
                    delta=s.delta or 0.0,
                    weight=s.weight,
                    score=s.score,
                    updated_at=rows[0].fetched_at.isoformat() if rows else "",
                )
            )

        return crisis_pb2.IndicatorsResponse(
            indicators=indicators_proto,
            total_score=total_score,
            calculated_at=datetime.utcnow().isoformat(),
        )

    async def GetNews(self, request, context):
        limit = request.limit or 20
        source_filter = request.source or None

        async with SessionLocal() as session:
            query = select(NewsItem).order_by(desc(NewsItem.published_at)).limit(limit)
            result = await session.execute(query)
            rows = result.scalars().all()

        items = []
        for r in rows:
            if source_filter and r.source != source_filter:
                continue
            items.append(
                crisis_pb2.NewsItem(
                    id=str(r.id),
                    title=r.title,
                    summary=r.summary or "",
                    source=r.source,
                    url=r.url,
                    published_at=r.published_at.isoformat() if r.published_at else "",
                )
            )

        return crisis_pb2.NewsResponse(items=items)
