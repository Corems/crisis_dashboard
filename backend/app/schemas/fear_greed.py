from pydantic import BaseModel


class FearGreedOut(BaseModel):
    score: float
    rating: str
    previous_close: float | None
    one_week_ago: float | None
    one_month_ago: float | None
    fetched_at: str
