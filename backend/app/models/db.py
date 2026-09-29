import os
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/crisisdb"
)

engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Indicator(Base):
    __tablename__ = "indicators"
    __table_args__ = (UniqueConstraint("fred_id", "date", name="uq_indicator_fred_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fred_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(256))
    value: Mapped[float] = mapped_column(Float)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NewsItem(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True)
    source: Mapped[str] = mapped_column(String(128))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(128))
    price: Mapped[float] = mapped_column(Float)
    change_pct: Mapped[float] = mapped_column(Float)
    change_week_pct: Mapped[float] = mapped_column(Float)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EconomicEvent(Base):
    __tablename__ = "economic_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_economic_event_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(128), index=True)  # unique id from Finnhub
    name: Mapped[str] = mapped_column(String(256))
    country: Mapped[str] = mapped_column(String(8))
    event_date: Mapped[datetime] = mapped_column(DateTime)
    impact: Mapped[str] = mapped_column(String(16))  # low / medium / high
    actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BuffettFiling(Base):
    __tablename__ = "buffett_filings"
    __table_args__ = (UniqueConstraint("accession_number", name="uq_buffett_filing_accession"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accession_number: Mapped[str] = mapped_column(String(32), index=True)
    filing_date: Mapped[str] = mapped_column(String(16))  # "YYYY-MM-DD"
    period_of_report: Mapped[str] = mapped_column(String(16))  # "YYYY-MM-DD"
    total_value_usd: Mapped[float] = mapped_column(Float)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BuffettHolding(Base):
    __tablename__ = "buffett_holdings"
    __table_args__ = (
        UniqueConstraint("accession_number", "company_name", name="uq_buffett_holding"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accession_number: Mapped[str] = mapped_column(String(32), index=True)
    filing_date: Mapped[str] = mapped_column(String(16))
    ticker: Mapped[str] = mapped_column(String(16))
    company_name: Mapped[str] = mapped_column(String(256))
    value_usd: Mapped[float] = mapped_column(Float)
    shares: Mapped[int] = mapped_column(Integer)
    portfolio_pct: Mapped[float] = mapped_column(Float)
    change_type: Mapped[str] = mapped_column(String(16))  # new/increased/decreased/unchanged
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ManagerFiling(Base):
    __tablename__ = "manager_filings"
    __table_args__ = (
        UniqueConstraint("manager_key", "accession_number", name="uq_manager_filing"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manager_key: Mapped[str] = mapped_column(String(32), index=True)  # bridgewater/scion/pershing
    manager_name: Mapped[str] = mapped_column(String(128))
    accession_number: Mapped[str] = mapped_column(String(32), index=True)
    filing_date: Mapped[str] = mapped_column(String(16))
    period_of_report: Mapped[str] = mapped_column(String(16))
    total_value_usd: Mapped[float] = mapped_column(Float)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ManagerHolding(Base):
    __tablename__ = "manager_holdings"
    __table_args__ = (
        UniqueConstraint(
            "manager_key", "accession_number", "company_name", name="uq_manager_holding"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manager_key: Mapped[str] = mapped_column(String(32), index=True)
    accession_number: Mapped[str] = mapped_column(String(32), index=True)
    filing_date: Mapped[str] = mapped_column(String(16))
    ticker: Mapped[str] = mapped_column(String(16))
    company_name: Mapped[str] = mapped_column(String(256))
    value_usd: Mapped[float] = mapped_column(Float)
    shares: Mapped[int] = mapped_column(Integer)
    portfolio_pct: Mapped[float] = mapped_column(Float)
    change_type: Mapped[str] = mapped_column(String(16))
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FedBalance(Base):
    __tablename__ = "fed_balance"
    __table_args__ = (UniqueConstraint("period", "series_id", name="uq_fed_balance_period_series"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    series_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(256))
    value_bln: Mapped[float] = mapped_column(Float)
    wow_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    wow_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    yoy_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    yoy_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CpiComponent(Base):
    __tablename__ = "cpi_components"
    __table_args__ = (UniqueConstraint("period", "series_id", name="uq_cpi_period_series"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    series_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(256))
    value: Mapped[float] = mapped_column(Float)
    yoy_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    mom_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CotReport(Base):
    __tablename__ = "cot_report"
    __table_args__ = (
        UniqueConstraint("report_date", "instrument", name="uq_cot_report_date_instrument"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, index=True)
    instrument: Mapped[str] = mapped_column(String(32))  # crude_oil / gold / sp500 / euro
    noncomm_long: Mapped[int] = mapped_column(Integer)
    noncomm_short: Mapped[int] = mapped_column(Integer)
    noncomm_net: Mapped[int] = mapped_column(Integer)
    noncomm_net_pct_oi: Mapped[float | None] = mapped_column(Float, nullable=True)
    comm_long: Mapped[int] = mapped_column(Integer)
    comm_short: Mapped[int] = mapped_column(Integer)
    open_interest: Mapped[int] = mapped_column(Integer)
    net_change_wow: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EiaPetroleum(Base):
    __tablename__ = "eia_petroleum"
    __table_args__ = (
        UniqueConstraint("period", "product", name="uq_eia_petroleum_period_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[date] = mapped_column(Date, index=True)
    product: Mapped[str] = mapped_column(String(32))  # crude / gasoline / distillate
    value_mbbl: Mapped[float] = mapped_column(Float)
    wow_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    wow_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    five_year_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FearGreed(Base):
    __tablename__ = "fear_greed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    score: Mapped[float] = mapped_column(Float)
    rating: Mapped[str] = mapped_column(String(64))
    previous_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    one_week_ago: Mapped[float | None] = mapped_column(Float, nullable=True)
    one_month_ago: Mapped[float | None] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IndexComparison(Base):
    __tablename__ = "index_comparison"
    __table_args__ = (
        UniqueConstraint("ticker", "period", name="uq_index_comparison_ticker_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(32), index=True)  # sp500 / msci_world
    period: Mapped[str] = mapped_column(String(8))  # 1mo / 3mo / ytd / 1y
    return_pct: Mapped[float] = mapped_column(Float)
    current_price: Mapped[float] = mapped_column(Float)
    chart_data: Mapped[list] = mapped_column(JSON)  # [{date, value}]
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketSignals(Base):
    __tablename__ = "market_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Entry signals
    vix: Mapped[float | None] = mapped_column(Float, nullable=True)
    vix_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    fear_greed_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fear_greed_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    sp500_current: Mapped[float | None] = mapped_column(Float, nullable=True)
    sp500_ma200: Mapped[float | None] = mapped_column(Float, nullable=True)
    sp500_above_ma200: Mapped[bool] = mapped_column(Boolean, default=False)
    cape: Mapped[float | None] = mapped_column(Float, nullable=True)
    cape_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    cot_crude_net: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cot_crude_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    green_count: Mapped[int] = mapped_column(Integer, default=0)
    overall_signal: Mapped[str] = mapped_column(String(16), default="WAIT")
    # Drawdown
    sp500_ath: Mapped[float | None] = mapped_column(Float, nullable=True)
    sp500_drawdown_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    msci_ath: Mapped[float | None] = mapped_column(Float, nullable=True)
    msci_current: Mapped[float | None] = mapped_column(Float, nullable=True)
    msci_drawdown_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AiAnalysis(Base):
    __tablename__ = "ai_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    situation: Mapped[str] = mapped_column(Text)
    whales: Mapped[str] = mapped_column(Text)
    signals: Mapped[list] = mapped_column(JSON)
    risk_level: Mapped[str] = mapped_column(String(16))
    risk_explanation: Mapped[str] = mapped_column(Text)
    investor_action: Mapped[str] = mapped_column(Text)
    raw_prompt: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_cached: Mapped[bool] = mapped_column(Boolean, default=False)


class StockAnalysis(Base):
    __tablename__ = "stock_analysis"
    __table_args__ = (UniqueConstraint("ticker", name="uq_stock_analysis_ticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    financial_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Valuation
    pe_trailing: Mapped[float | None] = mapped_column(Float, nullable=True)
    pe_forward: Mapped[float | None] = mapped_column(Float, nullable=True)
    pb: Mapped[float | None] = mapped_column(Float, nullable=True)
    ps: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_ebitda: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    peg: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Profitability
    profit_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    oper_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    roe: Mapped[float | None] = mapped_column(Float, nullable=True)
    roa: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Growth
    rev_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    earn_growth: Mapped[float | None] = mapped_column(Float, nullable=True)
    rev_qtr_growth: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Health
    debt_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    quick_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    fcf: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cash: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_debt: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Per-share
    eps_trailing: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps_forward: Mapped[float | None] = mapped_column(Float, nullable=True)
    book_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Context
    beta: Mapped[float | None] = mapped_column(Float, nullable=True)
    div_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    payout_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Analysis
    analysis: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
