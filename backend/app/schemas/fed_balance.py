from pydantic import BaseModel


class FedBalanceOut(BaseModel):
    period: str
    series_id: str
    name: str
    value_bln: float
    wow_change: float | None
    wow_change_pct: float | None
    yoy_change: float | None
    yoy_change_pct: float | None
