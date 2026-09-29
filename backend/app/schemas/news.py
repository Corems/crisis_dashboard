from pydantic import BaseModel


class NewsItemOut(BaseModel):
    id: int
    title: str
    summary: str | None
    source: str
    url: str
    published_at: str | None
