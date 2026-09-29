from pydantic import BaseModel


class CpiComponentOut(BaseModel):
    period: str
    series_id: str
    name: str
    value: float
    yoy_change_pct: float | None
    mom_change_pct: float | None
