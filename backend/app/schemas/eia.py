from pydantic import BaseModel


class EiaPetroleumOut(BaseModel):
    period: str
    product: str
    value_mbbl: float
    wow_change: float | None
    wow_change_pct: float | None
    five_year_avg: float | None
