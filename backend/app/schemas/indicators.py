from pydantic import BaseModel


class HintOut(BaseModel):
    what: str
    how: str
    impact: str


class IndicatorOut(BaseModel):
    fred_id: str
    name: str
    category: str
    value: float
    delta: float | None
    weight: float
    score: float
    hint: HintOut | None
    date: str | None = None
    fetched_at: str | None = None
    update_frequency: str | None = None
    inverted: bool = False


class IndicatorsOut(BaseModel):
    indicators: list[IndicatorOut]
    total_score: float
    calculated_at: str
