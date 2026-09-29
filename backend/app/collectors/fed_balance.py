import os
from datetime import datetime

import httpx

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

FED_SERIES: dict[str, str] = {
    "WALCL": "ФРС: Загальні активи",
    "WRESERVES": "ФРС: Резерви банків",
    "WTREGEN": "ФРС: Казначейські облігації",
    "WMBSEC": "ФРС: Іпотечні цінні папери (MBS)",
    "RRPONTSYD": "ФРС: Зворотне РЕПО (овернайт)",
    "WLRRAL": "ФРС: Позики (BTFP + дисконтне вікно)",
}


async def fetch_series(client: httpx.AsyncClient, series_id: str, name: str) -> list[dict]:

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 105,
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
        for i, (period, value) in enumerate(parsed[:104]):
            wow_change = None
            wow_change_pct = None
            if i + 1 < len(parsed):
                prev = parsed[i + 1][1]
                if prev:
                    wow_change = value - prev
                    wow_change_pct = wow_change / prev * 100

            yoy_change = None
            yoy_change_pct = None
            if i + 52 < len(parsed):
                yr_ago = parsed[i + 52][1]
                if yr_ago:
                    yoy_change = value - yr_ago
                    yoy_change_pct = yoy_change / yr_ago * 100

            rows.append(
                {
                    "period": period,
                    "series_id": series_id,
                    "name": name,
                    "value_bln": value,
                    "wow_change": wow_change,
                    "wow_change_pct": wow_change_pct,
                    "yoy_change": yoy_change,
                    "yoy_change_pct": yoy_change_pct,
                    "created_at": now,
                }
            )

        return rows

    except Exception as e:
        print(f"FedBalance fetch error [{series_id}]: {e}")
        return []


async def collect_all() -> list[dict]:

    import asyncio

    async with httpx.AsyncClient() as client:
        tasks = [fetch_series(client, sid, name) for sid, name in FED_SERIES.items()]
        results = await asyncio.gather(*tasks)

    collected = []
    for series_id, rows in zip(FED_SERIES.keys(), results, strict=True):
        if not rows:
            print(f"FedBalance: no data for {series_id}, skipping")
            continue
        collected.extend(rows)
        print(f"FedBalance: computed {len(rows)} rows for {series_id}")

    return collected
