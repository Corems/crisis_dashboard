import json
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "indicators.json"


def load_yahoo_config() -> list[dict]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return [item for item in raw if item.get("source") == "yahoo"]


async def collect_yahoo() -> list[dict]:

    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    import yfinance as yf

    config = load_yahoo_config()

    def fetch_ticker(item: dict) -> dict | None:
        ticker = item["fred_id"]
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if hist.empty:
                print(f"Yahoo: no data for {ticker}")
                return None

            current = float(hist["Close"].iloc[-1])
            previous = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current

            return {
                "fred_id": ticker,
                "name": item["name"],
                "value": round(current, 4),
                "previous_value": round(previous, 4),
                "weight": item["weight"],
                "fetched_at": datetime.utcnow(),
            }
        except Exception as e:
            print(f"Yahoo fetch error [{ticker}]: {e}")
            return None

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        tasks = [loop.run_in_executor(pool, fetch_ticker, item) for item in config]
        results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]
