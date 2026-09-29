from datetime import date


async def collect_and_save() -> dict:
    from sqlalchemy import select

    from app.collectors.pmi_scraper import collect_pmi
    from app.models.db import Indicator, SessionLocal, init_db
    from app.services.indicators import INDICATORS_CONFIG, calculate_score

    await init_db()
    raw = await collect_pmi()

    if not raw:
        return {"status": "error", "message": "Scrape failed for all PMI indicators"}

    saved = []
    async with SessionLocal() as session:
        for item in raw:
            fred_id = item["fred_id"]

            config = INDICATORS_CONFIG.get(fred_id)
            weight = config["weight"] if config else 10

            scored_list, _ = calculate_score(
                [
                    {
                        **item,
                        "weight": weight,
                    }
                ]
            )
            score = scored_list[0].score if scored_list else 0.0

            stmt = select(Indicator).where(
                Indicator.fred_id == fred_id, Indicator.date == date.today()
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.value = item["value"]
                existing.previous_value = item["previous_value"]
                existing.weight = weight
                existing.score = score
                existing.fetched_at = item["fetched_at"]
            else:
                session.add(
                    Indicator(
                        fred_id=fred_id,
                        name=item["name"],
                        value=item["value"],
                        previous_value=item["previous_value"],
                        weight=weight,
                        score=score,
                        date=date.today(),
                        fetched_at=item["fetched_at"],
                    )
                )

            saved.append({"fred_id": fred_id, "value": item["value"]})

        await session.commit()

    return {"status": "ok", "saved": saved}
