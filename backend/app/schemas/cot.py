from pydantic import BaseModel


class CotReportOut(BaseModel):
    report_date: str
    instrument: str
    noncomm_long: int
    noncomm_short: int
    noncomm_net: int
    noncomm_net_pct_oi: float | None
    comm_long: int
    comm_short: int
    open_interest: int
    net_change_wow: int | None
