from datetime import datetime

from fastapi import FastAPI

from app.models.db import init_db


def create_rest_app() -> FastAPI:
    app = FastAPI(title="Crisis Dashboard API", version="0.1.0")

    @app.on_event("startup")
    async def startup():
        await init_db()

    @app.get("/health")
    async def health():
        return {"status": "ok", "time": datetime.utcnow().isoformat()}

    from app.api.routes import (
        analysis,
        buffett,
        chat,
        collect,
        cot,
        cpi,
        eia,
        events,
        fear_greed,
        fed_balance,
        index_comparison,
        indicators,
        managers,
        news,
        signals,
        stock,
    )

    app.include_router(indicators.router)
    app.include_router(news.router)
    app.include_router(events.router)
    app.include_router(buffett.router)
    app.include_router(managers.router)
    app.include_router(eia.router)
    app.include_router(cot.router)
    app.include_router(fed_balance.router)
    app.include_router(cpi.router)
    app.include_router(analysis.router)
    app.include_router(fear_greed.router)
    app.include_router(signals.router)
    app.include_router(index_comparison.router)
    app.include_router(stock.router)
    app.include_router(chat.router)
    app.include_router(collect.router)

    return app
