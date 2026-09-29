import json
import os
import re
from datetime import datetime
from pathlib import Path

import anthropic
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LONGCAT_API_KEY = os.getenv("LONGCAT_API_KEY", "")

CONFIG_PATH = Path(__file__).parent.parent / "config" / "analyst_config.json"


def _load_config() -> dict:

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"analyst_config.json not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Context collection
# ---------------------------------------------------------------------------


async def _collect_context(session: AsyncSession) -> dict:
    from app.models.db import (
        BuffettFiling,
        BuffettHolding,
        CotReport,
        CpiComponent,
        EiaPetroleum,
        FearGreed,
        FedBalance,
        Indicator,
        ManagerFiling,
        ManagerHolding,
        NewsItem,
    )
    from app.services.indicators import calculate_score

    ctx: dict = {}

    # 1. Crisis score + indicators
    subq = select(func.max(Indicator.id).label("max_id")).group_by(Indicator.fred_id).subquery()
    result = await session.execute(select(Indicator).where(Indicator.id.in_(select(subq))))
    indicators = result.scalars().all()
    raw = [
        {
            "fred_id": r.fred_id,
            "name": r.name,
            "value": r.value,
            "previous_value": r.previous_value,
            "weight": r.weight,
            "score": r.score,
        }
        for r in indicators
    ]
    scored, total = calculate_score(raw)
    ctx["crisis_score"] = total
    ctx["indicators"] = sorted(scored, key=lambda x: x.score, reverse=True)[:10]

    # 2. COT latest
    cot_subq = (
        select(func.max(CotReport.report_date).label("max_date"), CotReport.instrument)
        .group_by(CotReport.instrument)
        .subquery()
    )
    result = await session.execute(
        select(CotReport).join(
            cot_subq,
            (CotReport.instrument == cot_subq.c.instrument)
            & (CotReport.report_date == cot_subq.c.max_date),
        )
    )
    ctx["cot"] = result.scalars().all()

    # 3. EIA latest
    eia_subq = (
        select(func.max(EiaPetroleum.period).label("max_period"), EiaPetroleum.product)
        .group_by(EiaPetroleum.product)
        .subquery()
    )
    result = await session.execute(
        select(EiaPetroleum).join(
            eia_subq,
            (EiaPetroleum.product == eia_subq.c.product)
            & (EiaPetroleum.period == eia_subq.c.max_period),
        )
    )
    ctx["eia"] = result.scalars().all()

    # 4. CPI latest
    cpi_subq = (
        select(func.max(CpiComponent.period).label("max_period"), CpiComponent.series_id)
        .group_by(CpiComponent.series_id)
        .subquery()
    )
    result = await session.execute(
        select(CpiComponent).join(
            cpi_subq,
            (CpiComponent.series_id == cpi_subq.c.series_id)
            & (CpiComponent.period == cpi_subq.c.max_period),
        )
    )
    ctx["cpi"] = result.scalars().all()

    # 5. Fed balance latest
    fed_subq = (
        select(func.max(FedBalance.period).label("max_period"), FedBalance.series_id)
        .group_by(FedBalance.series_id)
        .subquery()
    )
    result = await session.execute(
        select(FedBalance).join(
            fed_subq,
            (FedBalance.series_id == fed_subq.c.series_id)
            & (FedBalance.period == fed_subq.c.max_period),
        )
    )
    ctx["fed"] = result.scalars().all()

    # 6. Buffett top 5
    filing_result = await session.execute(
        select(BuffettFiling).order_by(desc(BuffettFiling.filing_date)).limit(1)
    )
    filing = filing_result.scalar_one_or_none()
    if filing:
        hr = await session.execute(
            select(BuffettHolding)
            .where(BuffettHolding.accession_number == filing.accession_number)
            .order_by(desc(BuffettHolding.portfolio_pct))
            .limit(5)
        )
        ctx["buffett"] = {"filing": filing, "holdings": hr.scalars().all()}
    else:
        ctx["buffett"] = None

    # 7. Manager top 3 per manager
    ctx["managers"] = {}
    for manager_key in ["bridgewater", "scion", "pershing"]:
        mf_result = await session.execute(
            select(ManagerFiling)
            .where(ManagerFiling.manager_key == manager_key)
            .order_by(desc(ManagerFiling.filing_date))
            .limit(1)
        )
        mf = mf_result.scalar_one_or_none()
        if mf:
            mh_result = await session.execute(
                select(ManagerHolding)
                .where(ManagerHolding.manager_key == manager_key)
                .where(ManagerHolding.accession_number == mf.accession_number)
                .order_by(desc(ManagerHolding.portfolio_pct))
                .limit(3)
            )
            ctx["managers"][manager_key] = {"filing": mf, "holdings": mh_result.scalars().all()}

    # 8. Latest 7 news
    news_result = await session.execute(
        select(NewsItem).order_by(desc(NewsItem.published_at)).limit(7)
    )
    ctx["news"] = news_result.scalars().all()

    # 9. Fear & Greed latest
    fg_result = await session.execute(
        select(FearGreed).order_by(desc(FearGreed.fetched_at)).limit(1)
    )
    ctx["fear_greed"] = fg_result.scalar_one_or_none()

    return ctx


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _build_prompt(ctx: dict) -> str:
    lines = ["=== MACROECONOMIC DASHBOARD DATA ===\n", f"CRISIS SCORE: {ctx['crisis_score']}/100\n"]

    lines.append("=== FRED INDICATORS (top by risk contribution) ===")
    for ind in ctx["indicators"]:
        delta = f" (Δ {ind.delta:+.4f})" if ind.delta is not None else ""
        lines.append(f"- {ind.name}: {ind.value:.4f}{delta} | score: {ind.score:.2f}/{ind.weight}")
    lines.append("")

    if ctx["cot"]:
        lines.append("=== COT POSITIONS ===")
        for r in ctx["cot"]:
            sentiment = "BULLISH" if r.noncomm_net > 0 else "BEARISH"
            wow = f" (WoW: {r.net_change_wow:+,})" if r.net_change_wow else ""
            pct = f" {r.noncomm_net_pct_oi:+.1f}% OI" if r.noncomm_net_pct_oi else ""
            lines.append(f"- {r.instrument}: net {r.noncomm_net:+,}{wow}{pct} — {sentiment}")
        lines.append("")

    if ctx["eia"]:
        lines.append("=== EIA PETROLEUM STOCKS ===")
        for r in ctx["eia"]:
            vs_avg = ""
            if r.five_year_avg:
                pct = (r.value_mbbl - r.five_year_avg) / r.five_year_avg * 100
                vs_avg = f" (vs 5yr avg: {pct:+.1f}%)"
            wow = f", WoW: {r.wow_change:+.1f} Mbbl" if r.wow_change else ""
            lines.append(f"- {r.product}: {r.value_mbbl:.1f} Mbbl{wow}{vs_avg}")
        lines.append("")

    if ctx["cpi"]:
        lines.append("=== CPI COMPONENTS ===")
        for r in ctx["cpi"]:
            yoy = f" YoY: {r.yoy_change_pct:+.2f}%" if r.yoy_change_pct else ""
            mom = f", MoM: {r.mom_change_pct:+.2f}%" if r.mom_change_pct else ""
            lines.append(f"- {r.name}:{yoy}{mom}")
        lines.append("")

    if ctx["fed"]:
        lines.append("=== FED BALANCE SHEET ===")
        for r in ctx["fed"]:
            wow = f", WoW: {r.wow_change:+.0f}B$" if r.wow_change else ""
            yoy = f", YoY: {r.yoy_change:+.0f}B$" if r.yoy_change else ""
            val = r.value_bln / 1000 if r.value_bln >= 1000 else r.value_bln
            unit = "T$" if r.value_bln >= 1000 else "B$"
            lines.append(f"- {r.name}: {val:.2f}{unit}{wow}{yoy}")
        lines.append("")

    if ctx["buffett"]:
        filing = ctx["buffett"]["filing"]
        lines.append(f"=== WARREN BUFFETT 13F (period: {filing.period_of_report}) ===")
        for h in ctx["buffett"]["holdings"]:
            lines.append(
                f"- {h.ticker} ({h.company_name[:30]}): {h.portfolio_pct:.1f}% | {h.change_type}"
            )
        lines.append("")

    if ctx["managers"]:
        NAMES = {
            "bridgewater": "Bridgewater/Dalio",
            "scion": "Scion/Burry",
            "pershing": "Pershing/Ackman",
        }
        lines.append("=== LARGE HEDGE FUND MANAGERS (13F) ===")
        for key, data in ctx["managers"].items():
            lines.append(f"{NAMES.get(key, key)} (period: {data['filing'].period_of_report}):")
            for h in data["holdings"]:
                lines.append(
                    f"  - {h.ticker} ({h.company_name[:25]}): {h.portfolio_pct:.1f}% | {h.change_type}"
                )
        lines.append("")

    if ctx.get("fear_greed"):
        fg = ctx["fear_greed"]
        lines.append("=== CNN FEAR & GREED INDEX ===")
        lines.append(f"- Current: {fg.score:.1f}/100 — {fg.rating.upper()}")
        if fg.previous_close:
            lines.append(f"- Previous close: {fg.previous_close:.1f}")
        if fg.one_week_ago:
            lines.append(f"- 1 week ago: {fg.one_week_ago:.1f}")
        if fg.one_month_ago:
            lines.append(f"- 1 month ago: {fg.one_month_ago:.1f}")
        lines.append("")

    if ctx["news"]:
        lines.append("=== LATEST NEWS HEADLINES ===")
        for n in ctx["news"]:
            lines.append(f"- [{n.source}] {n.title}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# AI response parsing
# ---------------------------------------------------------------------------


def _parse_ai_response(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()

    try:
        data = json.loads(text)
        return {
            "situation": str(data.get("situation", "")),
            "whales": str(data.get("whales", "")),
            "signals": list(data.get("signals", [])),
            "risk_level": str(data.get("risk_level", "moderate")),
            "risk_explanation": str(data.get("risk_explanation", "")),
            "investor_action": str(data.get("investor_action", "")),
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "situation": text,
            "whales": "",
            "signals": [],
            "risk_level": "moderate",
            "risk_explanation": "Не вдалося розібрати відповідь AI",
            "investor_action": "",
        }


# ---------------------------------------------------------------------------
# Provider calls
# ---------------------------------------------------------------------------


async def _call_anthropic(prompt: str, model: str, system_prompt: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=model,
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_ai_response(message.content[0].text)


async def _call_longcat(prompt: str, model: str, system_prompt: str) -> dict:
    if not LONGCAT_API_KEY:
        raise ValueError("LONGCAT_API_KEY not configured")
    from app.services.longcat import call_longcat

    resp = await call_longcat(
        api_key=LONGCAT_API_KEY,
        model=model,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )
    content = resp.get("content", [{}])
    text = content[0].get("text", "") if content else ""
    return _parse_ai_response(text)


async def _call_ai(
    prompt: str,
    config: dict,
    provider_override: str | None = None,
    model_override: str | None = None,
) -> dict:
    provider = (provider_override or config.get("provider", "anthropic")).lower()
    system_prompt = config["system_prompt"]

    if provider == "longcat":
        model = model_override or config.get("longcat_model", "LongCat-Flash-Chat")
        print(f"AI analyst: calling LongCat API (model: {model})...")
        return await _call_longcat(prompt, model, system_prompt)
    elif provider == "anthropic":
        model = model_override or config.get("anthropic_model", "claude-sonnet-4-20250514")
        print(f"AI analyst: calling Anthropic API (model: {model})...")
        return await _call_anthropic(prompt, model, system_prompt)
    else:
        raise ValueError(f"Unknown provider '{provider}'. Use 'anthropic' or 'longcat'.")


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _row_to_dict(row, cached: bool) -> dict:
    return {
        "id": row.id,
        "situation": row.situation,
        "whales": row.whales,
        "signals": row.signals or [],
        "risk_level": row.risk_level,
        "risk_explanation": row.risk_explanation,
        "investor_action": row.investor_action,
        "generated_at": row.generated_at.isoformat(),
        "cached": cached,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def generate_analysis(
    force: bool = False,
    provider_override: str | None = None,
    model_override: str | None = None,
) -> dict:

    from app.models.db import AiAnalysis, SessionLocal, init_db

    await init_db()
    config = _load_config()

    cache_ttl_hours = config.get("cache_ttl_hours", 12)
    force_cooldown_hours = config.get("force_cooldown_hours", 24)

    async with SessionLocal() as session:
        result = await session.execute(
            select(AiAnalysis).order_by(desc(AiAnalysis.generated_at)).limit(1)
        )
        latest = result.scalar_one_or_none()

        if latest:
            age_hours = (datetime.utcnow() - latest.generated_at).total_seconds() / 3600

            if force and age_hours < force_cooldown_hours:
                hours_left = max(1, int(force_cooldown_hours - age_hours))
                raise ValueError(
                    f"Аналіз оновлено {int(age_hours)} год тому. Спробуйте через {hours_left} год."
                )

            if not force and age_hours < cache_ttl_hours:
                print(f"AI analyst: returning cached analysis ({age_hours:.1f}h old)")
                return _row_to_dict(latest, cached=True)

        ctx = await _collect_context(session)
        prompt = _build_prompt(ctx)

        parsed = await _call_ai(
            prompt,
            config=config,
            provider_override=provider_override,
            model_override=model_override,
        )

        row = AiAnalysis(
            situation=parsed["situation"],
            whales=parsed["whales"],
            signals=parsed["signals"],
            risk_level=parsed["risk_level"],
            risk_explanation=parsed["risk_explanation"],
            investor_action=parsed["investor_action"],
            raw_prompt=prompt[:8000],
            generated_at=datetime.utcnow(),
            is_cached=False,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        print("AI analyst: stored new analysis")
        return _row_to_dict(row, cached=False)
