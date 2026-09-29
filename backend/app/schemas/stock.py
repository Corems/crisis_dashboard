from pydantic import BaseModel


class YouTubeAnalyzeRequest(BaseModel):
    transcript: str


class YouTubeAnalyzeResponse(BaseModel):
    transcript: str
    analysis: str


class StockFundamentalsOut(BaseModel):
    ticker: str
    company_name: str | None
    sector: str | None
    industry: str | None
    market_cap: float | None
    currency: str | None
    financial_currency: str | None
    # valuation
    pe_trailing: float | None
    pe_forward: float | None
    pb: float | None
    ps: float | None
    ev_ebitda: float | None
    ev_revenue: float | None
    peg: float | None
    # profitability
    profit_margin: float | None
    oper_margin: float | None
    gross_margin: float | None
    roe: float | None
    roa: float | None
    # growth
    rev_growth: float | None
    earn_growth: float | None
    rev_qtr_growth: float | None
    # health
    debt_equity: float | None
    current_ratio: float | None
    quick_ratio: float | None
    fcf: float | None
    total_cash: float | None
    total_debt: float | None
    # per-share
    eps_trailing: float | None
    eps_forward: float | None
    book_value: float | None
    # context
    beta: float | None
    div_yield: float | None
    payout_ratio: float | None
    # analysis
    analysis: str
    fetched_at: str
    generated_at: str
    expires_at: str
    cached: bool
