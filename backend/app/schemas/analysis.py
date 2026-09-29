from pydantic import BaseModel


class AiAnalysisOut(BaseModel):
    id: int
    situation: str
    whales: str
    signals: list[str]
    risk_level: str
    risk_explanation: str
    investor_action: str
    generated_at: str
    cached: bool
