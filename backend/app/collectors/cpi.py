import os
from datetime import datetime

import httpx

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

CPI_SERIES: dict[str, str] = {
    "CPIAUCSL": "CPI: Загальна інфляція",
    "CPIENGSL": "CPI: Енергоносії",
    "CPIFABSL": "CPI: Продукти харчування",
    "CPIHOSSL": "CPI: Житло",
    "CPITRNSL": "CPI: Транспорт",
    "CPIMEDSL": "CPI: Медицина",
    "CUSR0000SACL1E": "CPI: Бензин",
}


async def fetch_series(client: httpx.AsyncClient, series_id: str, name: str) -> list[dict]:

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 25,
    }
    try:
        resp = await client.get(FRED_BASE, params=params, timeout=10)
        resp.raise_for_status()
        observations = resp.json().get("observations", [])

        parsed: list[tuple] = []
        for o in observations:
            if o["value"] == ".":
                continue
            try:
                period = datetime.strptime(o["date"], "%Y-%m-%d").date()
                value = float(o["value"])
                parsed.append((period, value))
            except (ValueError, KeyError):
                continue

        if not parsed:
            return []

        now = datetime.utcnow()
        rows = []
        for i, (period, value) in enumerate(parsed[:24]):
            mom_pct = None
            if i + 1 < len(parsed):
                prev = parsed[i + 1][1]
                if prev:
                    mom_pct = (value - prev) / prev * 100

            yoy_pct = None
            if i + 12 < len(parsed):
                yr_ago = parsed[i + 12][1]
                if yr_ago:
                    yoy_pct = (value - yr_ago) / yr_ago * 100

            rows.append(
                {
                    "period": period,
                    "series_id": series_id,
                    "name": name,
                    "value": value,
                    "yoy_change_pct": yoy_pct,
                    "mom_change_pct": mom_pct,
                    "created_at": now,
                }
            )

        return rows

    except Exception as e:
        print(f"CPI fetch error [{series_id}]: {e}")
        return []


async def collect_all() -> list[dict]:

    import asyncio

    async with httpx.AsyncClient() as client:
        tasks = [fetch_series(client, sid, name) for sid, name in CPI_SERIES.items()]
        results = await asyncio.gather(*tasks)

    collected = []
    for series_id, rows in zip(CPI_SERIES.keys(), results, strict=True):
        if not rows:
            print(f"CPI: no data for {series_id}, skipping")
            continue
        collected.extend(rows)
        print(f"CPI: computed {len(rows)} rows for {series_id}")

    return collected
