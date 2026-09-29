from pydantic import BaseModel


class MarketSignalsOut(BaseModel):
    vix: float | None
    vix_ok: bool
    fear_greed_score: float | None
    fear_greed_ok: bool
    sp500_current: float | None
    sp500_ma200: float | None
    sp500_above_ma200: bool
    cape: float | None
    cape_ok: bool
    cot_crude_net: int | None
    cot_crude_ok: bool
    green_count: int
    overall_signal: str
    sp500_ath: float | None
    sp500_drawdown_pct: float | None
    msci_ath: float | None
    msci_current: float | None
    msci_drawdown_pct: float | None
    fetched_at: str
