import asyncio
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


def _safe_float(val) -> float | None:

    if val is None:
        return None
    f = float(val)
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _fetch_vix() -> float | None:
    import yfinance as yf

    try:
        hist = yf.Ticker("^VIX").history(period="5d")
        if hist.empty:
            return None
        closes = hist["Close"].dropna()
        if closes.empty:
            return None
        val = _safe_float(closes.iloc[-1])
        return round(val, 2) if val is not None else None
    except Exception as e:
        print(f"MarketSignals VIX error: {e}")
        return None


def _fetch_sp500_extended() -> dict | None:

    import yfinance as yf

    try:
        hist = yf.Ticker("^GSPC").history(period="2y")
        if hist.empty or len(hist) < 10:
            return None
        closes = hist["Close"].dropna()
        if closes.empty:
            return None
        current = _safe_float(closes.iloc[-1])
        ma200 = (
            _safe_float(closes.iloc[-200:].mean())
            if len(closes) >= 200
            else _safe_float(closes.mean())
        )
        ath = _safe_float(closes.max())
        if current is None or ath is None:
            return None
        drawdown = round((current - ath) / ath * 100, 2) if ath != 0 else 0.0
        return {
            "current": round(current, 2),
            "ma200": round(ma200, 2) if ma200 is not None else None,
            "above_ma200": current > ma200 if ma200 is not None else False,
            "ath": round(ath, 2),
            "drawdown_pct": drawdown,
        }
    except Exception as e:
        print(f"MarketSignals SP500 error: {e}")
        return None


def _fetch_msci_ath() -> dict | None:
    import yfinance as yf

    try:
        hist = yf.Ticker("IWDA.L").history(period="2y")
        if hist.empty:
            return None
        closes = hist["Close"].dropna()
        if closes.empty:
            return None
        current = _safe_float(closes.iloc[-1])
        ath = _safe_float(closes.max())
        if current is None or ath is None:
            return None
        drawdown = round((current - ath) / ath * 100, 2) if ath != 0 else 0.0
        return {
            "current": round(current, 2),
            "ath": round(ath, 2),
            "drawdown_pct": drawdown,
        }
    except Exception as e:
        print(f"MarketSignals MSCI error: {e}")
        return None


def _fetch_cape() -> float | None:
    import re

    import requests

    try:
        resp = requests.get(
            "https://www.multpl.com/shiller-pe",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        # Value sits as bare text right after the id="current" block's <b>...</b>
        m = re.search(r'id="current"[^>]*>.*?</b>\s*([\d.]+)', resp.text, re.DOTALL)
        if not m:
            return None
        return round(float(m.group(1)), 2)
    except Exception as e:
        print(f"MarketSignals CAPE error: {e}")
        return None


async def collect_market_signals(session) -> dict:
    from sqlalchemy import desc, select

    from app.models.db import CotReport, FearGreed

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        vix, sp500, msci, cape = await asyncio.gather(
            loop.run_in_executor(pool, _fetch_vix),
            loop.run_in_executor(pool, _fetch_sp500_extended),
            loop.run_in_executor(pool, _fetch_msci_ath),
            loop.run_in_executor(pool, _fetch_cape),
        )

    # DB reads
    fg_row = (
        await session.execute(select(FearGreed).order_by(desc(FearGreed.fetched_at)).limit(1))
    ).scalar_one_or_none()
    fg_score = fg_row.score if fg_row else None

    cot_row = (
        await session.execute(
            select(CotReport)
            .where(CotReport.instrument == "crude_oil")
            .order_by(desc(CotReport.report_date))
            .limit(1)
        )
    ).scalar_one_or_none()
    cot_net = cot_row.noncomm_net if cot_row else None

    # Signal booleans
    vix_ok = vix is not None and vix < 20
    fg_ok = fg_score is not None and fg_score > 30
    sp500_above_ma200 = bool(sp500 and sp500["above_ma200"])
    cape_ok = cape is not None and cape < 25
    cot_ok = cot_net is not None and cot_net > 0

    green_count = sum([vix_ok, fg_ok, sp500_above_ma200, cape_ok, cot_ok])
    overall_signal = "WAIT" if green_count <= 1 else ("WATCH" if green_count <= 3 else "ENTER")

    return {
        "vix": vix,
        "vix_ok": vix_ok,
        "fear_greed_score": fg_score,
        "fear_greed_ok": fg_ok,
        "sp500_current": sp500["current"] if sp500 else None,
        "sp500_ma200": sp500["ma200"] if sp500 else None,
        "sp500_above_ma200": sp500_above_ma200,
        "cape": cape,
        "cape_ok": cape_ok,
        "cot_crude_net": cot_net,
        "cot_crude_ok": cot_ok,
        "green_count": green_count,
        "overall_signal": overall_signal,
        "sp500_ath": sp500["ath"] if sp500 else None,
        "sp500_drawdown_pct": sp500["drawdown_pct"] if sp500 else None,
        "msci_ath": msci["ath"] if msci else None,
        "msci_current": msci["current"] if msci else None,
        "msci_drawdown_pct": msci["drawdown_pct"] if msci else None,
        "fetched_at": datetime.utcnow(),
    }
