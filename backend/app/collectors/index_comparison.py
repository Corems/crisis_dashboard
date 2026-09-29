import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

TICKERS = {
    "sp500": "^GSPC",
    "msci_world": "IWDA.L",
}
PERIODS = ["1mo", "3mo", "ytd", "1y"]


def _fetch_ticker_period(ticker_key: str, ticker_symbol: str, period: str) -> dict | None:
    import yfinance as yf

    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period=period)
        if hist.empty or len(hist) < 2:
            print(f"IndexComparison: no data for {ticker_symbol} period={period}")
            return None

        closes = hist["Close"]
        first_close = float(closes.iloc[0])
        last_close = float(closes.iloc[-1])

        if first_close == 0:
            return None

        return_pct = (last_close - first_close) / first_close * 100

        chart_data = [
            {"date": str(idx.date()), "value": round(float(val) / first_close * 100, 2)}
            for idx, val in zip(closes.index, closes.values, strict=True)
        ]

        return {
            "ticker": ticker_key,
            "period": period,
            "return_pct": round(return_pct, 4),
            "current_price": round(last_close, 4),
            "chart_data": chart_data,
            "fetched_at": datetime.utcnow(),
        }
    except Exception as e:
        print(f"IndexComparison fetch error [{ticker_symbol} {period}]: {e}")
        return None


async def collect_index_comparison() -> list[dict]:
    loop = asyncio.get_event_loop()
    pairs = [
        (ticker_key, ticker_symbol, period)
        for ticker_key, ticker_symbol in TICKERS.items()
        for period in PERIODS
    ]

    with ThreadPoolExecutor() as pool:
        tasks = [
            loop.run_in_executor(pool, _fetch_ticker_period, key, sym, period)
            for key, sym, period in pairs
        ]
        results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]
