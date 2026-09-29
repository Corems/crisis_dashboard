import asyncio
from datetime import datetime, timedelta
from typing import Any

import yfinance as yf

from app.services.ai_client import AIClient

# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def _safe(val: Any, default=None):

    try:
        if val is None:
            return default
        import math

        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return default
        return val
    except Exception:
        return default


def fetch_fundamentals(ticker: str) -> dict:

    t = yf.Ticker(ticker.upper())
    info = t.info or {}

    # yfinance returns an empty/minimal dict for unknown tickers
    if not info.get("symbol") and not info.get("shortName"):
        raise ValueError(f"Ticker '{ticker}' not found or no data available")

    # --- Valuation ---
    pe_trailing = _safe(info.get("trailingPE"))
    pe_forward = _safe(info.get("forwardPE"))
    pb = _safe(info.get("priceToBook"))
    ps = _safe(info.get("priceToSalesTrailing12Months"))
    ev_ebitda = _safe(info.get("enterpriseToEbitda"))
    ev_revenue = _safe(info.get("enterpriseToRevenue"))
    peg = _safe(info.get("pegRatio"))

    # --- Profitability ---
    profit_margin = _safe(info.get("profitMargins"))
    oper_margin = _safe(info.get("operatingMargins"))
    gross_margin = _safe(info.get("grossMargins"))
    roe = _safe(info.get("returnOnEquity"))
    roa = _safe(info.get("returnOnAssets"))

    # --- Growth ---
    rev_growth = _safe(info.get("revenueGrowth"))  # YoY
    earn_growth = _safe(info.get("earningsGrowth"))  # YoY
    rev_qtr_growth = _safe(info.get("revenueQuarterlyGrowth"))

    # --- Financial health ---
    debt_equity = _safe(info.get("debtToEquity"))  # in %
    current_ratio = _safe(info.get("currentRatio"))
    quick_ratio = _safe(info.get("quickRatio"))
    fcf = _safe(info.get("freeCashflow"))  # absolute $
    total_cash = _safe(info.get("totalCash"))
    total_debt = _safe(info.get("totalDebt"))

    # --- Per-share ---
    eps_trailing = _safe(info.get("trailingEps"))
    eps_forward = _safe(info.get("forwardEps"))
    book_value = _safe(info.get("bookValue"))

    # --- Market context ---
    # --- Market context ---
    market_cap = _safe(info.get("marketCap"))
    currency = _safe(info.get("currency"), "USD")
    financial_currency = _safe(info.get("financialCurrency"), _safe(info.get("currency"), "USD"))
    beta = _safe(info.get("beta"))
    div_yield = _safe(info.get("dividendYield"))
    payout_ratio = _safe(info.get("payoutRatio"))
    sector = _safe(info.get("sector"), "")
    industry = _safe(info.get("industry"), "")
    company_name = _safe(info.get("longName") or info.get("shortName"), ticker.upper())

    return {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "market_cap": market_cap,
        "currency": currency,
        "financial_currency": financial_currency,
        # valuation
        "pe_trailing": pe_trailing,
        "pe_forward": pe_forward,
        "pb": pb,
        "ps": ps,
        "ev_ebitda": ev_ebitda,
        "ev_revenue": ev_revenue,
        "peg": peg,
        # profitability
        "profit_margin": profit_margin,
        "oper_margin": oper_margin,
        "gross_margin": gross_margin,
        "roe": roe,
        "roa": roa,
        # growth
        "rev_growth": rev_growth,
        "earn_growth": earn_growth,
        "rev_qtr_growth": rev_qtr_growth,
        # health
        "debt_equity": debt_equity,
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "fcf": fcf,
        "total_cash": total_cash,
        "total_debt": total_debt,
        # per-share
        "eps_trailing": eps_trailing,
        "eps_forward": eps_forward,
        "book_value": book_value,
        # context
        "beta": beta,
        "div_yield": div_yield,
        "payout_ratio": payout_ratio,
        "fetched_at": datetime.utcnow(),
    }


# ---------------------------------------------------------------------------
# Claude analysis
# ---------------------------------------------------------------------------


def _fmt(val, pct=False, x=False, usd=False, b=False) -> str:

    if val is None:
        return "N/A"
    if b:  # billions
        return f"${val / 1e9:.2f}B"
    if usd:
        return f"${val:,.0f}"
    if pct:
        return f"{val * 100:.1f}%"
    if x:
        return f"{val:.2f}x"
    return f"{val:.2f}"


def _build_prompt(data: dict) -> str:
    d = data

    currency_warning = ""
    if (
        d.get("currency")
        and d.get("financial_currency")
        and d["currency"] != d["financial_currency"]
    ):
        currency_warning = (
            f"\n⚠️ WARNING: Share price is in {d['currency']}, but financial statements "
            f"are in {d['financial_currency']}. Absolute figures (FCF, Cash, Debt, Market Cap) "
            f"may be in different currencies — do not compare them directly.\n"
        )

    return f"""You are a fundamental analyst. Analyze the stock based on real financial data.

## {d["company_name"]} ({d["ticker"]})
{currency_warning}
Sector: {d["sector"]} | Industry: {d["industry"]}
Market capitalization: {_fmt(d["market_cap"], b=True)}

## Valuation
| Multiple | Value |
|---|---|
| P/E (trailing) | {_fmt(d["pe_trailing"], x=True)} |
| P/E (forward) | {_fmt(d["pe_forward"], x=True)} |
| P/B | {_fmt(d["pb"], x=True)} |
| P/S | {_fmt(d["ps"], x=True)} |
| EV/EBITDA | {_fmt(d["ev_ebitda"], x=True)} |
| PEG | {_fmt(d["peg"], x=True)} |

## Profitability
| Metric | Value |
|---|---|
| Net margin | {_fmt(d["profit_margin"], pct=True)} |
| Operating margin | {_fmt(d["oper_margin"], pct=True)} |
| Gross margin | {_fmt(d["gross_margin"], pct=True)} |
| ROE | {_fmt(d["roe"], pct=True)} |
| ROA | {_fmt(d["roa"], pct=True)} |

## Growth (YoY)
| Metric | Value |
|---|---|
| Revenue | {_fmt(d["rev_growth"], pct=True)} |
| Earnings | {_fmt(d["earn_growth"], pct=True)} |

## Financial health
| Metric | Value |
|---|---|
| Debt/Equity | {_fmt(d["debt_equity"])}% |
| Current Ratio | {_fmt(d["current_ratio"], x=True)} |
| Quick Ratio | {_fmt(d["quick_ratio"], x=True)} |
| Free Cash Flow | {_fmt(d["fcf"], b=True)} |
| Cash | {_fmt(d["total_cash"], b=True)} |
| Debt | {_fmt(d["total_debt"], b=True)} |

## Other
EPS (trailing): {_fmt(d["eps_trailing"])} | EPS (forward): {_fmt(d["eps_forward"])}
Beta: {_fmt(d["beta"])} | Dividend yield: {_fmt(d["div_yield"], pct=True)}

---

Provide a structured analysis in Ukrainian:

### 1. Valuation (is the stock expensive or cheap?)
Compare multiples against typical values for the sector. State explicitly — overvalued, fairly valued, or undervalued. Do not say "decent" or "acceptable" without citing numbers.

### 2. Business quality
Assess margins and profitability. Is there a competitive advantage? Compare ROE against the cost of capital (approximately 10%).

### 3. Growth
Assess the rate of revenue and earnings growth. Does it justify the current valuation? Is growth sustainable?

### 4. Financial risk
Assess debt load and liquidity. Is there a risk of default? Is FCF sufficient?

### 5. Verdict
One sentence: what kind of company this is from a fundamental standpoint. No buy/sell recommendations.

Important: rely only on the numbers provided. Do not invent data that is not available. If a metric is N/A — state that there is insufficient data to assess that aspect.

Respond in Ukrainian."""


async def generate_analysis(data: dict) -> str:
    prompt = _build_prompt(data)
    return await AIClient().complete(prompt=prompt, system="", max_tokens=2048)


# ---------------------------------------------------------------------------
# Main entry point (called from endpoint)
# ---------------------------------------------------------------------------


async def analyze_stock(ticker: str) -> dict:
    loop = asyncio.get_event_loop()
    fundamentals = await loop.run_in_executor(None, fetch_fundamentals, ticker)
    analysis_text = await generate_analysis(fundamentals)  # already async, no executor needed

    return {
        **fundamentals,
        "analysis": analysis_text,
        "generated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24),
    }
