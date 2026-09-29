from pydantic import BaseModel


class ManagerHoldingOut(BaseModel):
    ticker: str
    company_name: str
    value_usd: float
    shares: int
    portfolio_pct: float
    change_type: str
    change_pct: float | None


class ManagerHoldingsOut(BaseModel):
    manager_key: str
    manager_name: str
    filing_date: str
    period_of_report: str
    total_value_usd: float
    holdings: list[ManagerHoldingOut]
