import json
import os
from datetime import datetime
from pathlib import Path

import httpx

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

CONFIG_PATH = Path(__file__).parent.parent / "config" / "indicators.json"


def load_config() -> list[dict]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return [item for item in raw if item.get("source", "fred") == "fred"]


INDICATORS_CONFIG = load_config()


async def fetch_two_latest(
    client: httpx.AsyncClient, fred_id: str
) -> tuple[float | None, float | None]:
    params = {
        "series_id": fred_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 2,
    }
    try:
        resp = await client.get(FRED_BASE, params=params, timeout=10)
        resp.raise_for_status()
        observations = resp.json().get("observations", [])
        values = [float(o["value"]) for o in observations if o["value"] != "."]
        current = values[0] if len(values) > 0 else None
        previous = values[1] if len(values) > 1 else None
        return current, previous
    except Exception as e:
        print(f"FRED fetch error [{fred_id}]: {e}")
        return None, None


async def collect_all() -> list[dict]:

    import asyncio

    async with httpx.AsyncClient() as client:
        tasks = [fetch_two_latest(client, ind["fred_id"]) for ind in INDICATORS_CONFIG]
        results = await asyncio.gather(*tasks)

    collected = []
    for ind, (current, previous) in zip(INDICATORS_CONFIG, results, strict=True):
        if current is None:
            print(f"Skipping {ind['fred_id']} — no data")
            continue
        collected.append(
            {
                "fred_id": ind["fred_id"],
                "name": ind["name"],
                "value": current,
                "previous_value": previous,
                "weight": ind["weight"],
                "fetched_at": datetime.utcnow(),
            }
        )

    return collected
