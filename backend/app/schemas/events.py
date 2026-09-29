from pydantic import BaseModel


class EconomicEventOut(BaseModel):
    event_id: str
    name: str
    country: str
    event_date: str
    impact: str
    actual: float | None
    estimate: float | None
    previous: float | None
    unit: str | None
