from pydantic import BaseModel


class ChartPoint(BaseModel):
    date: str
    value: float


class IndexPeriodData(BaseModel):
    ticker: str
    period: str
    return_pct: float
    current_price: float
    chart_data: list[ChartPoint]
    fetched_at: str
