from pydantic import BaseModel


class BuffettHoldingOut(BaseModel):
    ticker: str
    company_name: str
    value_usd: float
    shares: int
    portfolio_pct: float
    change_type: str
    change_pct: float | None


class BuffettHoldingsOut(BaseModel):
    filing_date: str
    period_of_report: str
    total_value_usd: float
    holdings: list[BuffettHoldingOut]


class BuffettFilingOut(BaseModel):
    accession_number: str
    filing_date: str
    period_of_report: str
    total_value_usd: float
    fetched_at: str
