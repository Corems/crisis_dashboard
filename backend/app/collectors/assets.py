from datetime import datetime

import yfinance as yf

ASSETS_CONFIG = [
    {"ticker": "^GSPC", "name": "S&P 500"},
    {"ticker": "GC=F", "name": "Gold"},
    {"ticker": "CL=F", "name": "WTI Oil"},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway B"},
    {"ticker": "^TNX", "name": "10Y Treasury Yield"},
]


def fetch_asset(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return None

        current = float(hist["Close"].iloc[-1])
        previous = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
        change_pct = ((current - previous) / previous) * 100

        week_ago = float(hist["Close"].iloc[0])
        change_week_pct = ((current - week_ago) / week_ago) * 100

        return {
            "ticker": ticker,
            "name": next(a["name"] for a in ASSETS_CONFIG if a["ticker"] == ticker),
            "price": round(current, 2),
            "change_pct": round(change_pct, 2),
            "change_week_pct": round(change_week_pct, 2),
            "fetched_at": datetime.utcnow(),
        }
    except Exception as e:
        print(f"Asset fetch error [{ticker}]: {e}")
        return None


async def collect_assets() -> list[dict]:
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        tasks = [loop.run_in_executor(pool, fetch_asset, a["ticker"]) for a in ASSETS_CONFIG]
        results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]
