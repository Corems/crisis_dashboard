import os
from datetime import datetime

import httpx

EIA_API_KEY = os.getenv("EIA_API_KEY", "")
EIA_BASE = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"

# EIA product codes for US national weekly petroleum stocks
PRODUCTS = {
    "crude": "EPC0",
    "gasoline": "EPM0",
    "distillate": "EPD0",
}


async def fetch_product(
    client: httpx.AsyncClient, product_code: str, length: int = 260
) -> list[dict]:
    params = {
        "frequency": "weekly",
        "data[0]": "value",
        "facets[product][]": product_code,
        "facets[duoarea][]": "NUS",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": length,
    }
    if EIA_API_KEY:
        params["api_key"] = EIA_API_KEY

    try:
        resp = await client.get(EIA_BASE, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("response", {}).get("data", [])
    except Exception as e:
        print(f"EIA fetch error [{product_code}]: {e}")
        return []


def _compute_rows(product_name: str, raw: list[dict], now: datetime) -> list[dict]:

    if len(raw) < 2:
        return []

    # Parse all entries once
    parsed = []
    for entry in raw:
        try:
            period = datetime.strptime(entry["period"], "%Y-%m-%d").date()
            value = float(entry["value"])
            parsed.append((period, value))
        except (ValueError, KeyError):
            continue

    if not parsed:
        return []

    # Build week-of-year → list of values for 5yr avg (all 260 weeks)
    from collections import defaultdict

    week_values: dict[int, list[float]] = defaultdict(list)
    for period, value in parsed:
        wk = period.isocalendar()[1]
        week_values[wk].append(value)

    rows = []
    for i, (period, value) in enumerate(parsed[:52]):
        prev_value = parsed[i + 1][1] if i + 1 < len(parsed) else None
        wow_change = (value - prev_value) if prev_value is not None else None
        wow_change_pct = (
            (wow_change / prev_value * 100) if (wow_change is not None and prev_value) else None
        )

        wk = period.isocalendar()[1]
        same_week = week_values[wk]
        five_year_avg = sum(same_week) / len(same_week) if same_week else None

        rows.append(
            {
                "period": period,
                "product": product_name,
                "value_mbbl": value,
                "wow_change": wow_change,
                "wow_change_pct": wow_change_pct,
                "five_year_avg": five_year_avg,
                "fetched_at": now,
            }
        )

    return rows


async def collect_all() -> list[dict]:

    import asyncio

    async with httpx.AsyncClient() as client:
        tasks = [fetch_product(client, code, length=260) for code in PRODUCTS.values()]
        results = await asyncio.gather(*tasks)

    now = datetime.utcnow()
    collected = []
    for product_name, raw in zip(PRODUCTS.keys(), results, strict=True):
        if not raw:
            print(f"EIA: no data for {product_name}, skipping")
            continue
        rows = _compute_rows(product_name, raw, now)
        collected.extend(rows)
        print(f"EIA: computed {len(rows)} rows for {product_name}")

    return collected
